import 'package:flutter/material.dart';

// Define the ProjectStats class
class ProjectStats {
  final int linesOfCode;
  final int conversations;
  final int filesCreated;
  final int complexity;

  ProjectStats({
    this.linesOfCode = 0,
    this.conversations = 0,
    this.filesCreated = 0,
    this.complexity = 0,
  });
}

class ProjectStatsChart extends StatelessWidget {
  final ProjectStats stats;
  final double width;
  final double height;

  const ProjectStatsChart({
    super.key,
    required this.stats,
    this.width = 250,
    this.height = 180,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Colors.grey[900], // Dark background
        borderRadius: BorderRadius.circular(12.0),
        border: Border.all(color: Colors.grey[700]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildStatItem('程式碼行數 (LOC)', stats.linesOfCode.toString(), Icons.code),
          _buildStatItem('對話次數 (Conversations)', stats.conversations.toString(), Icons.chat),
          _buildStatItem('檔案創建 (Files)', stats.filesCreated.toString(), Icons.insert_drive_file),
          _buildStatItem('複雜度 (Complexity)', stats.complexity.toString(), Icons.compare_arrows),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Colors.indigo[300]),
          const SizedBox(width: 8),
          Text(
            '$label:',
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 12,
            ),
          ),
          const Spacer(),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
