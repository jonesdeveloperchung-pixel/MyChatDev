import 'package:flutter/material.dart';
import 'package:flutter_app/widgets/chat_message.dart';

class ChatLog extends StatelessWidget {
  final List<Message> messages;
  final ScrollController scrollController;

  const ChatLog({
    super.key,
    required this.messages,
    required this.scrollController,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: scrollController,
      itemCount: messages.length,
      padding: const EdgeInsets.all(16.0),
      itemBuilder: (context, index) {
        return ChatMessage(message: messages[index]);
      },
    );
  }
}
