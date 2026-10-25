class CommunicationManager:

    @staticmethod
    def send_message(sender, receiver, message):
        """
        Send a message from one agent to another.
        """

        print(
            f"[COMMUNICATION] "
            f"{sender.agent_id} -> {receiver.agent_id}: {message}"
        )

        receiver.receive_message(
            sender,
            message
        )