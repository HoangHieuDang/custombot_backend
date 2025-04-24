from abc import ABC, abstractmethod
#CRUD Create Read Updater Delete

class DatabaseInterface(ABC):

    # Create Data
    @abstractmethod
    def add_user(self, user_infos):
        pass

    def add_custom_bot_to_user(self, user_id, bot_id):
        pass

    def add_part(self, part_infos):
        pass

    def add_part_to_custom_bot(self, part_id, bot_id):
        pass

    def add_order(self, user_id, bot_id, order_infos):
        pass

    # Read Data
    @abstractmethod
    def get_user(self,**criteria):
        pass

    @abstractmethod
    def get_custom_bot(self, **criteria):
        pass

    @abstractmethod
    def get_part(self, **criteria):
        pass

    @abstractmethod
    def get_order(self, **criteria):
        pass

    @abstractmethod
    def get_part_from_custom_bot(self, bot_id):
        pass


    # Update Data
    @abstractmethod
    def update_user(self, user_id, updated_infos):
        pass

    @abstractmethod
    def update_custom_bot(self, bot_id, updated_infos):
        pass

    @abstractmethod
    def update_bot_part(self, part_id, updated_infos):
        pass



    # Delete Data
    @abstractmethod
    def delete_user(self, user_id):
        pass

    @abstractmethod
    def delete_custom_bot_from_user(self, user_id, bot_id):
        pass

    @abstractmethod
    def delete_part(self, part_id):
        pass

    @abstractmethod
    def delete_order(self, order_id):
        pass

