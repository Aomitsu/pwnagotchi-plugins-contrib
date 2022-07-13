import os
import logging
import requests
from requests.auth import HTTPBasicAuth
import os
from pwnagotchi.voice import Voice
import pwnagotchi.plugins as plugins


class PleromaStatus(plugins.Plugin):
    __author__ = 'maxime@s.echapp.com'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Periodically post status updates. Based on mastodon plugin by siina@siina.dev who based this plugin on twitter plugin by evilsocket'

    def on_loaded(self):
        logging.info("pleroma plugin loaded.")

    # Called when there's available internet
    def on_internet_available(self, agent):
        config = agent.config()
        display = agent.view()
        last_session = agent.last_session
        api_version_url = '/api/v1/'
        api_base_url = self.options['instance_url'] + api_version_url
        username = self.options['username']
        password = self.options['password']
        visibility = self.options['visibility']
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

        if last_session.is_new() and last_session.handshakes > 0:
            logging.info("Detected internet and new activity: time to post!")

            # Pleroma allow login with Basic HTTP Auth
            # From mastodon plugin : Get pwnagotchi picture and save to a file
            picture = '/root/pwnagotchi.png'
            display.on_manual_mode(last_session)
            display.image().save(picture, 'png')
            display.update(force=True)
            message = Voice(lang=config['main']['lang']).on_last_session_tweet(last_session)

            try:
                logging.info('Sending picture with Pleroma API')
                with open(picture, 'rb') as img:
                    name_img = os.path.basename(picture)
                    files = {'file': (name_img, img, 'multipart/form-data', {'Expires': '0'})}
                    with requests.Session() as s:
                        headers = {'Accept': 'application/json'}
                        media = requests.post(api_base_url+'media',
                                              auth=HTTPBasicAuth(username, password),
                                              files=files,
                                              headers=headers
                                              )
                        json = media.json()
                        print(json)

                        r = requests.post(api_base_url+'statuses',
                                          auth=HTTPBasicAuth(username, password),
                                          json={"status": message,
                                                "visibility": visibility,
                                                "media_ids": [json["id"].replace("'", '"')]},
                                          headers=headers)
                        print(r.json())
                        print(r.request.body)
                        print(r.status_code)

                last_session.save_session_id()
                logging.info("posted: %s" % message)
                display.set('status', 'Posted!')
                display.update(force=True)
            except Exception:
                logging.exception("error while posting")
