import pickle
import logging
import os

BACKUP_FILENAME_PREFIX = "backup_"
BACKUP_DIRECTORY = "/.data_backup"

class Backup:
    def __init__(self, service_name, get_backupable_user_state, get_backupable_middleware_state):
        self._service_name = service_name
        self._get_backupable_user_state = get_backupable_user_state
        self._get_backupable_middleware_state = get_backupable_middleware_state

    def __get_backup_filename(self):
        backup_filename = f"{BACKUP_DIRECTORY}/{self._service_name}.backup"
        return backup_filename

    def stage(self):
        backupable_middleware_state = self._get_backupable_middleware_state()
        backupable_user_state = self._get_backupable_user_state()

        backup_data = {
            "middleware": backupable_middleware_state,
            "user": backupable_user_state,
        }
        
        compressed_backup_data = pickle.dumps(backup_data)

        backup_filename = self.__get_backup_filename()
        
        try:
            with open(f"{backup_filename}.tmp",'wb') as backup_file:
                backup_file.write(compressed_backup_data)
                backup_file.flush()
        except Exception as e:
            logging.warn(f"Problem staging backup state: {e}")
    
    def commit(self):
        backup_filename = self.__get_backup_filename()

        try:
            os.rename(f"{backup_filename}.tmp", backup_filename)
        except Exception as e:
            logging.warn(f"Problem committing backup state: {e}")

    def __create_backup_file(self):
        if not os.path.exists(self.__get_backup_filename()):
            base_content = pickle.dumps({})
            with open(self.__get_backup_filename(), "wb") as f:
                f.write(base_content)

    def recover_backup_state(self, key):
        # Key must be either 'middleware' or 'user'
        backup_filename = self.__get_backup_filename()
        if not os.path.exists(backup_filename):
            self.__create_backup_file()
            return
        
        try:
            with open(backup_filename,'rb') as backup_file:
                backup_data = backup_file.read()
            
            backup_state = pickle.loads(backup_data)
            
            return backup_state[key]
        
        except KeyError as e:
            logging.warn(f"Backup key not found. If this is the first time the system is run, ignore this: {e}")
        except Exception as e:
            logging.warn(f"Problem restoring backed up state with key {key}: {e}")