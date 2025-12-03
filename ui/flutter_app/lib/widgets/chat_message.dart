import 'package:flutter/material.dart';

// Define the Message class
enum MessageSenderType {
  user,
  agent,
  system,
}

enum Phase {
  idle,
  demandAnalysis,
  languageChoice,
  coding,
  codeReview,
  testing,
  completed,
  // Add other phases as needed
}


class Message {
  final String id;
  final MessageSenderType senderType; // new field to differentiate user/agent
  final String role; // now a string for dynamic agent roles
  final String content;
  final DateTime timestamp;
  final Phase phase;

  Message({
    required this.id,
    required this.senderType,
    required this.role,
    required this.content,
    required this.timestamp,
    required this.phase,
  });
}

class ChatMessage extends StatelessWidget {
  final Message message;

  const ChatMessage({super.key, required this.message});

  // Helper to map role string to a representative IconData
  IconData _getIconForRole(String role) {
    switch (role) {
      case "product_manager": return Icons.layers_outlined;
      case "architect": return Icons.design_services;
      case "tester": return Icons.bug_report_outlined;
      case "programmer": return Icons.code;
      case "reviewer": return Icons.rate_review_outlined;
      case "quality_gate": return Icons.check_circle_outline;
      case "reflector": return Icons.lightbulb_outline;
      case "distiller": return Icons.compress;
      case "user": return Icons.person_outline;
      default: return Icons.person; // Default icon
    }
  }

  // Helper to map role string to a representative Color
  Color _getColorForRole(String role) {
    switch (role) {
      case "product_manager": return Colors.green;
      case "architect": return Colors.blue;
      case "tester": return Colors.teal;
      case "programmer": return Colors.purple;
      case "reviewer": return Colors.red;
      case "quality_gate": return Colors.orange;
      case "reflector": return Colors.yellow;
      case "distiller": return Colors.grey;
      case "user": return Colors.blueGrey;
      default: return Colors.indigo; // Default color
    }
  }

  @override
  Widget build(BuildContext context) {
    // Determine if the message is from the user or an agent
    final bool isUser = message.senderType == MessageSenderType.user;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 10.0),
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: isUser ? Colors.blueGrey[700] : Colors.grey[800],
        borderRadius: BorderRadius.circular(12.0),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Agent icon/avatar
              CircleAvatar(
                backgroundColor: _getColorForRole(message.role),
                child: Icon(
                  _getIconForRole(message.role),
                  color: Colors.white,
                  size: 20,
                ),
              ),
              const SizedBox(width: 10.0),
              // Role and timestamp
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    message.role, // Display role name directly
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: isUser ? Colors.white : _getColorForRole(message.role),
                    ),
                  ),
                  Text(
                    '${message.timestamp.hour}:${message.timestamp.minute}', // Simple timestamp
                    style: const TextStyle(color: Colors.grey, fontSize: 10.0),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 10.0),
          // Message content
          Text(
            message.content,
            style: const TextStyle(color: Colors.white70),
          ),
          // Optional: Phase indicator (can be more elaborate later)
          if (message.phase != Phase.idle)
            Padding(
              padding: const EdgeInsets.only(top: 8.0),
              child: Text(
                'Phase: ${message.phase.toString().split('.').last}',
                style: const TextStyle(color: Colors.green, fontSize: 10.0),
              ),
            ),
        ],
      ),
    );
  }
}
