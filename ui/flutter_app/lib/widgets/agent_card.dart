import 'package:flutter/material.dart';

class AgentCard extends StatelessWidget {
  final String name;
  final String role;
  final IconData icon;
  final Color color;
  final bool isActive;

  const AgentCard({
    super.key,
    required this.name,
    required this.role,
    required this.icon,
    required this.color,
    this.isActive = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 120,
      height: 150,
      decoration: BoxDecoration(
        color: isActive ? color.withAlpha((255 * 0.2).round()) : Colors.grey[800],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isActive ? color : Colors.transparent,
          width: 2,
        ),
        boxShadow: isActive
            ? [
                BoxShadow(
                  color: color.withAlpha((255 * 0.3).round()),
                  blurRadius: 10,
                  spreadRadius: 2,
                ),
              ]
            : [],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            icon,
            size: 40,
            color: isActive ? color : Colors.white,
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4.0),
            child: Text(
              name,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: isActive ? color : Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4.0),
            child: Text(
              role,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: isActive ? color.withAlpha((255 * 0.7).round()) : Colors.grey[400],
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
