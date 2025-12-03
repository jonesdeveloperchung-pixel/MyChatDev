import 'package:flutter/material.dart';

class LoadingIndicator extends StatefulWidget {
  const LoadingIndicator({super.key});

  @override
  State<LoadingIndicator> createState() => _LoadingIndicatorState();
}

class _LoadingIndicatorState extends State<LoadingIndicator> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation1;
  late Animation<double> _animation2;
  late Animation<double> _animation3;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..repeat();

    _animation1 = Tween(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.7, curve: Curves.easeInOut),
      ),
    );
    _animation2 = Tween(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.1, 0.8, curve: Curves.easeInOut),
      ),
    );
    _animation3 = Tween(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.2, 0.9, curve: Curves.easeInOut),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Widget _buildDot(Animation<double> animation) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) {
        return Opacity(
          opacity: animation.value < 0.5 ? animation.value * 2 : (1 - animation.value) * 2, // Simple pulse
          child: Container(
            width: 8, // w-2 (tailwind) * 4 = 8px
            height: 8, // h-2 (tailwind) * 4 = 8px
            decoration: BoxDecoration(
              color: Colors.indigo[400], // text-indigo-400
              shape: BoxShape.circle,
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8), // px-4 py-2
      decoration: BoxDecoration(
        color: Colors.grey[800], // bg-gray-800
        borderRadius: BorderRadius.circular(999), // rounded-full
        border: Border.all(color: Colors.indigo.shade900.withAlpha((255 * 0.5).round())), // border-indigo-900/50
        boxShadow: [
          BoxShadow(
            color: const Color.fromRGBO(0, 0, 0, 0.2), // shadow-lg
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildDot(_animation1),
          const SizedBox(width: 4),
          _buildDot(_animation2),
          const SizedBox(width: 4),
          _buildDot(_animation3),
          const SizedBox(width: 8),
          const Text(
            'PyMaestro 正在執行...',
            style: TextStyle(
              color: Color(0xFF818CF8), // text-indigo-400
              fontSize: 12, // text-xs
              fontWeight: FontWeight.w600, // font-mono
            ),
          ),
        ],
      ),
    );
  }
}
