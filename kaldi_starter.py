import os
import redis
import json
import multiprocessing as mp
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


def start_kaldi(server, input, output, controlChannel, speaker, language):
    if language == 'German':
        model = 'kaldi_tuda_de_nnet3_chain2.yaml'
        kaldiDir = f'docker exec kamose asr -m 0 -e -t -y ./models/{model} --redis-server={server} --redis-audio={input} --redis-channel={output} --redis-control={controlChannel} -s="{speaker}" -fpc 190'
    else:
        onlineConf = 'en_160k_nnet3chain_tdnn1f_2048_sp_bi/conf/online.conf'
        model = 'en_160k_nnet3chain_tdnn1f_2048_sp_bi.yaml'
        kaldiDir = 'docker exec kamose asr -m 0 -e -t -o models/%s -y models/%s --redis-server=%s --redis-audio=%s --redis-channel=%s --redis-control=%s -s="%s" -fpc 190' % (onlineConf, model, server, input, output, controlChannel, speaker)
    os.system(kaldiDir)


def wait_for_channel(server, port, channel):
    red = redis.Redis(host=server, port=port, password=os.getenv("REDIS_PASSWORD"))
    pubsub = red.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(channel)

    while True:
        time.sleep(0.2)
        message = pubsub.get_message()
        try:
            if message:
                message = json.loads(message['data'].decode('UTF-8'))
                logging.info(json.dumps(message, indent=2))
                callerUsername = message['Caller-Username']
                language = message['Language']
                audioChannel = message['Audio-Channel']
                textChannel = message['Text-Channel']
                controlChannel = message['Control-Channel']
                callerDestinationNumber = message['Caller-Destination-Number']
                origCallerIDName = message['Caller-Orig-Caller-ID-Name']
                if message['Event'] == 'LOADER_START':
                    logging.info('Start Kaldi')
                    p = mp.Process(target=start_kaldi, args=(server, audioChannel, textChannel, controlChannel, callerUsername, language))
                    p.start()
                    # kaldiInstances[audioChannel] = p
                    redis_channel_message(red, channel, 'KALDI_START', callerDestinationNumber, origCallerIDName, callerUsername, language, audioChannel, textChannel, controlChannel)
                    
                if message['Event'] == 'LOADER_STOP':
                    audioChannel = message['Audio-Channel']
                    controlChannel = message['Control-Channel']
                    
                    kaldi_shutdown(red, audioChannel, controlChannel)
                    redis_channel_message(red, channel, 'KALDI_STOP', callerDestinationNumber, origCallerIDName, callerUsername, language, audioChannel, textChannel, controlChannel)
                
        except Exception as e:
            logging.info(e)
            pass


def kaldi_shutdown(red, audioChannel, controlChannel):
    logger.info('Stop Kaldi')
    red.publish(controlChannel, 'shutdown')
    time.sleep(0.5)
    red.publish(audioChannel, 8*'\x00')
    time.sleep(0.5)
    red.publish(audioChannel, 8*'\x00')

def redis_channel_message(red, channel, Event, callerDestinationNumber, origCallerIDName, callerUsername, language, inputChannel, outputChannel, controlChannel):
    message = {
                'Event': Event,
                'Caller-Destination-Number': callerDestinationNumber,
                'Caller-Orig-Caller-ID-Name': origCallerIDName,
                'Caller-Username': callerUsername,
                'Language': language,
                'Audio-Channel': inputChannel,
                'Text-Channel': outputChannel,
                'Control-Channel': controlChannel
    }
    red.publish(channel, json.dumps(message))


if __name__ == '__main__':
    wait_for_channel("localhost", 6379, "asr_channel")
