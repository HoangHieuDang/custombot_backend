from abc import ABC, abstractmethod


# CRUD Create Read Updater Delete

class DatabaseInterface(ABC):

    # Create Data
    @abstractmethod
    def add_user(self, users_list):
        pass
    @abstractmethod
    def add_part(self, parts_list):
        pass
    @abstractmethod
    def create_custom_bot_for_user(self, bots_list):
        pass
    @abstractmethod
    def add_part_to_custom_bot(self, part_id, custom_robot_id, amount):
        pass
    @abstractmethod
    def add_order(self, orders_list):
        pass


    # Read Data
    @abstractmethod
    def get_user(self, **criteria):
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
    def get_parts_from_custom_bot(self, bot_id):
        pass

    # Update Data
    @abstractmethod
    def update_user(self, user_id, **changes):
        pass

    @abstractmethod
    def update_custom_bot(self, bot_id, **changes):
        pass

    @abstractmethod
    def update_bot_part(self, part_id, **changes):
        pass

    @abstractmethod
    def update_order(self, order_id, **changes):
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
