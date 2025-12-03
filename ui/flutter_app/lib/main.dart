import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async'; // Import for Timer
import 'package:flutter_app/widgets/agent_card.dart';
import 'package:flutter_app/widgets/project_stats_chart.dart';
import 'package:flutter_app/widgets/loading_indicator.dart';
import 'package:flutter_app/widgets/chat_message.dart';
import 'package:flutter_app/widgets/chat_log.dart';
import 'package:flutter_app/custom_sse_client.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ChatDev-X Flutter UI',
      theme: ThemeData(
        brightness: Brightness.dark, // Dark theme
        scaffoldBackgroundColor: const Color(0xFF0A0A0A), // Equivalent to bg-gray-950
        // Define text themes and other colors later
      ),
      home: const ChatDevXScreen(),
    );
  }
}

// Define Agent class matching backend response structure
class Agent {
  final String name;
  final String displayName;
  final String description;
  final IconData icon;
  final Color color;

  Agent({
    required this.name,
    required this.displayName,
    required this.description,
    required this.icon,
    required this.color,
  });

  factory Agent.fromJson(Map<String, dynamic> json) {
    return Agent(
      name: json['name'],
      displayName: json['display_name'],
      description: json['description'],
      icon: _mapMaterialIcon(json['icon']),
      color: _mapColor(json['color']),
    );
  }
}

// Helper to map string icon names to Material Design Icons
IconData _mapMaterialIcon(String iconName) {
  switch (iconName) {
    case 'person_outline': return Icons.person_outline;
    case 'layers_outlined': return Icons.layers_outlined;
    case 'bug_report_outlined': return Icons.bug_report_outlined;
    case 'code': return Icons.code;
    case 'rate_review_outlined': return Icons.rate_review_outlined;
    case 'check_circle_outline': return Icons.check_circle_outline;
    case 'lightbulb_outline': return Icons.lightbulb_outline;
    case 'compress': return Icons.compress;
    case 'design_services': return Icons.design_services;
    default: return Icons.person;
  }
}

// Helper to map string color names to Flutter Colors
Color _mapColor(String colorName) {
  switch (colorName) {
    case 'blue': return Colors.blue;
    case 'green': return Colors.green;
    case 'teal': return Colors.teal;
    case 'purple': return Colors.purple;
    case 'red': return Colors.red;
    case 'orange': return Colors.orange;
    case 'yellow': return Colors.yellow;
    case 'grey': return Colors.grey;
    case 'blueGrey': return Colors.blueGrey; // Used for user messages
    default: return Colors.indigo;
  }
}


class ChatDevXScreen extends StatefulWidget {
  const ChatDevXScreen({super.key});

  @override
  State<ChatDevXScreen> createState() => _ChatDevXScreenState();
}

class _ChatDevXScreenState extends State<ChatDevXScreen> {
  String _currentPage = 'welcome';
  String _domain = 'Software';
  String _language = 'zh-Hant';
  String _selectedLlmProfile = '';
  String _task = "設計一個貪吃蛇遊戲 (Snake Game) 使用 Python。";
  bool _isRunning = false;
  String? _currentWorkflowRunId; // To store the run_id for stopping or status checks
  Timer? _statusTimer; // Timer for polling workflow status
  StreamSubscription<SseEvent>? _sseSubscription; // SSE Stream subscription

  // State for displaying current workflow status
  String _currentPhase = 'IDLE';
  int _currentSteps = 0;
  int _currentLoc = 0;
  String _activeAgentName = 'user'; // Mock active agent name, corresponds to activeAgent in React App.tsx
  
  // System Health State
  bool _isOllamaRunning = false;
  String _ollamaVersion = '';

  List<Agent> _agents = []; // Dynamic list of agents

  List<String> _llmProfiles = []; // Now a mutable list

  // State for Add LLM Profile dialog
  final _profileNameController = TextEditingController();
  final _modelIdController = TextEditingController();
  final _providerController = TextEditingController();
  final _apiKeyController = TextEditingController();
  final _baseUrlController = TextEditingController();

  // State for Global Settings
  final _ollamaHostController = TextEditingController();
  final _maxIterationsController = TextEditingController();
  bool _enableSandbox = false;
  bool _humanApproval = false;

  // ProjectStats will be updated dynamically from workflow status, but keep it for UI structure
  ProjectStats _projectStats = ProjectStats(
    linesOfCode: 0,
    conversations: 0,
    filesCreated: 0,
    complexity: 0, // Not directly from workflow status yet
  );

  final List<Message> _messages = [
    // Initial mock messages
    Message(
      id: '1',
      senderType: MessageSenderType.user,
      role: "user",
      content: "設計一個貪吃蛇遊戲 (Snake Game) 使用 Python。",
      timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
      phase: Phase.idle,
    ),
  ];
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _checkOllamaStatus(); // Check Ollama status first
    _fetchRoles(); // Fetch roles on initialization
    _fetchLlmProfiles(); // Fetch LLM profiles on initialization
    _fetchConfig(); // Fetch global config on initialization
    _startStatusPolling(); // Start polling on init
  }

  Future<void> _checkOllamaStatus() async {
    try {
      final response = await http.get(Uri.parse('http://127.0.0.1:8000/system/ollama_status'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _isOllamaRunning = data['is_running'] ?? false;
          _ollamaVersion = data['version'] ?? '';
        });
        if (!_isOllamaRunning) {
           ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('⚠️ Ollama is not detected! Please ensure Ollama app is running.'),
              backgroundColor: Colors.orange,
              duration: Duration(seconds: 10),
            ),
          );
        }
      }
    } catch (e) {
      print('Error checking Ollama status: $e');
      setState(() {
        _isOllamaRunning = false;
      });
    }
  }

  @override
  void dispose() {
    _statusTimer?.cancel(); // Cancel timer on dispose
    _sseSubscription?.cancel(); // Cancel SSE subscription
    _profileNameController.dispose();
    _modelIdController.dispose();
    _providerController.dispose();
    _apiKeyController.dispose();
    _baseUrlController.dispose();
    _ollamaHostController.dispose();
    _maxIterationsController.dispose();
    super.dispose();
  }

  // Function to fetch roles from the FastAPI backend
  Future<void> _fetchRoles() async {
    try {
      final response = await http.get(Uri.parse('http://127.0.0.1:8000/roles')); // Assuming API runs locally on 8000
      if (response.statusCode == 200) {
        List<dynamic> rolesJson = json.decode(response.body);
        setState(() {
          _agents = rolesJson.map((json) => Agent.fromJson(json)).toList();
        });
      } else {
        // Handle error: show a snackbar or log the error
        print('Failed to load roles: ${response.statusCode}');
      }
    } catch (e) {
      // Handle network error
      print('Error fetching roles: $e');
    }
  }

  // New Function to fetch LLM Profiles from the FastAPI backend
  Future<void> _fetchLlmProfiles() async {
    try {
      final response = await http.get(Uri.parse('http://127.0.0.1:8000/profiles'));
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> profilesJson = data['profiles'];
        setState(() {
          _llmProfiles = profilesJson.map((profile) => profile['name'] as String).toList();
          if (_llmProfiles.isNotEmpty && !_llmProfiles.contains(_selectedLlmProfile)) {
            _selectedLlmProfile = _llmProfiles[0]; // Set default if previous selection is invalid
          } else if (_llmProfiles.isEmpty) {
            _selectedLlmProfile = ''; // Clear if no profiles
          }
        });
      } else {
        print('Failed to load LLM profiles: ${response.statusCode}');
      }
    } catch (e) {
      // Handle network error
      print('Error fetching LLM profiles: $e');
    }
  }

  // New Function to fetch Global Config from the FastAPI backend
  Future<void> _fetchConfig() async {
    try {
      final response = await http.get(Uri.parse('http://127.0.0.1:8000/config'));
      if (response.statusCode == 200) {
        final Map<String, dynamic> configData = json.decode(response.body);
        setState(() {
          _ollamaHostController.text = configData['ollama_host'] ?? '';
          _maxIterationsController.text = configData['max_iterations']?.toString() ?? '5';
          _enableSandbox = configData['enable_sandbox'] ?? false;
          _humanApproval = configData['human_approval'] ?? false;
        });
      } else {
        print('Failed to load config: ${response.statusCode}');
      }
    } catch (e) {
      // Handle network error
      print('Error fetching config: $e');
    }
  }

  // Start polling mechanism
  void _startStatusPolling() {
    _statusTimer = Timer.periodic(const Duration(seconds: 2), (timer) { // Poll every 2 seconds
      if (_isRunning && _currentWorkflowRunId != null) {
        _fetchWorkflowStatus();
      }
    });
  }

  // Fetch workflow status from API
  Future<void> _fetchWorkflowStatus() async {
    if (_currentWorkflowRunId == null) return;

    try {
      final response = await http.get(Uri.parse('http://127.0.0.1:8000/workflow/status/$_currentWorkflowRunId'));
      if (response.statusCode == 200) {
        final Map<String, dynamic> statusData = json.decode(response.body);
        setState(() {
          // Update current phase, steps, etc.
          _currentPhase = statusData['current_phase'] ?? (statusData['status'] == 'completed' ? 'COMPLETED' : 'UNKNOWN');
          _currentSteps = statusData['iteration_count'] ?? 0;
          _currentLoc = statusData['deliverables']?['code']?.length ?? 0; // Assuming code length can represent LOC
          _activeAgentName = statusData['active_agent'] ?? 'user'; // Needs actual active agent from backend

          // Update project stats chart
          _projectStats = ProjectStats(
            linesOfCode: _currentLoc,
            conversations: _currentSteps, // Using iterations as conversations
            filesCreated: 0, // Placeholder
            complexity: 0, // Placeholder
          );
          
          if (statusData['status'] == 'completed' || statusData['should_halt'] == true) {
            _isRunning = false;
            _statusTimer?.cancel();
            _currentWorkflowRunId = null; // Clear run ID once completed
            _currentPhase = 'COMPLETED';
          }
        });
      } else if (response.statusCode == 404) {
        print('Workflow status not found for run ID: $_currentWorkflowRunId. It might have finished or failed.');
        setState(() {
          _isRunning = false;
          _statusTimer?.cancel();
          _currentWorkflowRunId = null;
          _currentPhase = 'IDLE'; // Reset
        });
      }
      else {
        print('Failed to fetch workflow status: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching workflow status: $e');
    }
  }

  // Function to start the workflow
  Future<void> _startWorkflow() async {
    if (!_isOllamaRunning) {
      _showErrorDialog(
        'Ollama Service Not Detected',
        'Please start the Ollama application on your machine to proceed.\n\nDownload it from ollama.com if you haven\'t installed it yet.'
      );
      return;
    }

    if (_selectedLlmProfile.isEmpty || _task.isEmpty) {
      // Show error to user
      print("Please select an LLM profile and enter a task.");
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select an LLM profile and enter a task.')),
      );
      return;
    }

    setState(() {
      _isRunning = true;
      _messages.clear(); // Clear previous messages
      _messages.add(Message(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        senderType: MessageSenderType.user,
        role: "user",
        content: _task,
        timestamp: DateTime.now(),
        phase: Phase.idle,
      ));
      _currentPhase = 'Starting...'; // Update UI feedback
      _currentSteps = 0;
      _currentLoc = 0;
    });

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:8000/workflow/start'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'user_prompt': _task,
          'profile_name': _selectedLlmProfile,
          // Add other configurable parameters from UI if implemented
          // For MVP, hardcode some defaults or use config from API
          'max_iterations': 5, // Example
          'enable_sandbox': true, // Example
          'log_level': 'INFO', // Example
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> responseData = json.decode(response.body);
        _currentWorkflowRunId = responseData['run_id'] as String?; // Store run_id
        print('Workflow started successfully. Run ID: $_currentWorkflowRunId');
        // Start polling for status updates
        _statusTimer?.cancel(); // Cancel any existing timer
        _startStatusPolling();
        // Start SSE stream
        _startSseStream();
      } else {
        final errorData = json.decode(response.body);
        print('Failed to start workflow: ${response.statusCode} - ${errorData['detail']}');
        setState(() {
          _isRunning = false;
          _currentPhase = 'Error';
        });
      }
    } catch (e) {
      print('Error starting workflow: $e');
      setState(() {
        _isRunning = false;
        _currentPhase = 'Error';
      });
    }
  }

  // Function to stop the workflow
  Future<void> _stopWorkflow() async {
    if (_currentWorkflowRunId == null) {
      print("No active workflow to stop.");
      setState(() {
        _isRunning = false;
        _currentPhase = 'IDLE';
      });
      return;
    }

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:8000/workflow/stop'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'run_id': _currentWorkflowRunId!,
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> responseData = json.decode(response.body);
        print('Workflow stop requested: ${responseData['message']}');
        setState(() {
          _isRunning = false;
          _currentWorkflowRunId = null;
          _currentPhase = 'IDLE';
          _statusTimer?.cancel();
        });
      } else if (response.statusCode == 501) {
        final errorData = json.decode(response.body);
        print('Stop not implemented: ${errorData['detail']}');
        // Even if not implemented on backend, UI reflects stopped state
        setState(() {
          _isRunning = false;
          _currentWorkflowRunId = null;
          _currentPhase = 'IDLE (Stop Not Supported)';
          _statusTimer?.cancel();
        });
      }
      else {
        final errorData = json.decode(response.body);
        print('Failed to stop workflow: ${response.statusCode} - ${errorData['detail']}');
      }
    } catch (e) {
      print('Error stopping workflow: $e');
    }
  }


  // Function to start the SSE stream
  void _startSseStream() {
    if (_currentWorkflowRunId == null) return;

    final sseUrl = 'http://127.0.0.1:8000/workflow/stream?run_id=$_currentWorkflowRunId';
    final customSseClient = CustomSseClient(sseUrl);

    _sseSubscription?.cancel(); // Cancel previous subscription if any
    _sseSubscription = customSseClient.connect().listen(
      (SseEvent event) {
        // Process the SSE event
        try {
          // Assuming event.data is a JSON string representing a message or log
          final eventData = json.decode(event.data);
          // Determine message type and format for ChatMessage
          // Example structure: {"type": "log", "content": "..."} or {"type": "agent_message", "role": "...", "content": "..."}

          Message newMessage;
          if (eventData['type'] == 'agent_message') {
            newMessage = Message(
              id: event.id ?? DateTime.now().millisecondsSinceEpoch.toString(),
              senderType: MessageSenderType.agent,
              role: eventData['role'] ?? 'unknown_agent',
              content: eventData['content'] ?? '',
              timestamp: DateTime.now(),
              phase: Phase.values.firstWhere(
                  (e) => e.toString().split('.').last == (eventData['phase'] ?? 'idle'),
                  orElse: () => Phase.idle),
            );
          } else if (eventData['type'] == 'node_execution') {
            // Update active agent and status for real-time feedback
            String nodeName = eventData['node'] ?? 'unknown';
            // Remove generic prefixes like 'agent_' if your nodes are named like that,
            // or just use the raw node name if it matches your role definitions.
            // Assuming nodes are named e.g. "product_manager", "architect".
            
            setState(() {
              _activeAgentName = nodeName;
              _currentPhase = 'Executing Node: $nodeName';
            });
            return; // Don't add a chat message for every node execution start, just update UI state
          } else { // Default to system log or generic message
            newMessage = Message(
              id: event.id ?? DateTime.now().millisecondsSinceEpoch.toString(),
              senderType: MessageSenderType.system,
              role: eventData['type'] ?? 'system_log',
              content: eventData['content'] ?? event.data, // Fallback to raw data
              timestamp: DateTime.now(),
              phase: Phase.values.firstWhere(
                  (e) => e.toString().split('.').last == (eventData['phase'] ?? 'idle'),
                  orElse: () => Phase.idle),
            );
          }

          setState(() {
            _messages.add(newMessage);
          });
          _scrollToBottom(); // Scroll chat to bottom after new message
        } catch (e) {
          print('Error processing SSE event: $e, Data: ${event.data}');
          setState(() {
            _messages.add(Message(
              id: DateTime.now().millisecondsSinceEpoch.toString(),
              senderType: MessageSenderType.system,
              role: 'sse_error',
              content: 'Error processing stream data: ${event.data}',
              timestamp: DateTime.now(),
              phase: Phase.idle,
            ));
          });
          _scrollToBottom();
        }
      },
      onError: (error) {
        print('SSE Stream Error: $error');
        setState(() {
          _messages.add(Message(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            senderType: MessageSenderType.system,
            role: 'sse_connection_error',
            content: 'SSE connection error: $error',
            timestamp: DateTime.now(),
            phase: Phase.idle,
          ));
        });
        _scrollToBottom();
        _isRunning = false; // Stop workflow UI if SSE fails
        _statusTimer?.cancel();
      },
      onDone: () {
        print('SSE Stream Done.');
        setState(() {
          _messages.add(Message(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            senderType: MessageSenderType.system,
            role: 'sse_connection_closed',
            content: 'SSE stream closed.',
            timestamp: DateTime.now(),
            phase: Phase.idle,
          ));
        });
        _scrollToBottom();
        _isRunning = false; // Stop workflow UI if SSE closes
        _statusTimer?.cancel();
      },
    );
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          Container(
            width: 320, // Equivalent to w-80 (80 * 4 = 320px)
            color: const Color(0xFF171717), // Equivalent to bg-gray-900
            child: Column(
              children: [
                // Header section in sidebar (Fixed at top)
                Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 32,
                            height: 32,
                            decoration: BoxDecoration(
                              color: const Color(0xFF4F46E5),
                              borderRadius: BorderRadius.circular(8.0),
                            ),
                            child: const Icon(Icons.terminal, color: Colors.white, size: 20),
                          ),
                          const SizedBox(width: 12),
                          const Text(
                            'ChatDev-X',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '智慧軟體開發代理架構 v3.0',
                        style: TextStyle(
                          fontSize: 10,
                          color: Color(0xFF6B7280),
                        ),
                      ),
                    ],
                  ),
                ),
                const Divider(color: Color(0xFF374151), height: 1),

                // Scrollable Content (Stats, Nav, Config)
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      children: [
                        // Project Stats Chart
                        Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: ProjectStatsChart(stats: _projectStats),
                        ),
                        const Divider(color: Color(0xFF374151), height: 1),

                        // Navigation
                        Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            children: [
                              _buildNavItem('welcome', Icons.dashboard, '儀表板 (Dashboard)'),
                              _buildNavItem('new-workflow', Icons.play_arrow, '新增任務 (New Task)'),
                              _buildNavItem('workflow-status', Icons.terminal, '執行狀態 (Workflow Status)'),
                              _buildNavItem('pending-approvals', Icons.settings_input_component, '審核 (Approvals)', hasBadge: true),
                              _buildNavItem('llm-profiles', Icons.settings_applications, 'LLM 設定 (LLM Profiles)'),
                              _buildNavItem('settings', Icons.settings, '全局設定 (Global Settings)'),
                              _buildNavItem('past-workflows', Icons.code, '歷史任務 (Past Tasks)'),
                            ],
                          ),
                        ),
                        const Divider(color: Color(0xFF374151), height: 1),

                        // Configuration and Task Input
                        Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              // Domain Selector
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    '領域設定 (Domain)',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF6B7280),
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  DropdownButtonFormField<String>(
                                    initialValue: _domain,
                                    items: const [
                                      DropdownMenuItem(value: 'Software', child: Text('💻 軟體開發 (Software)')),
                                      DropdownMenuItem(value: 'Game', child: Text('🎮 遊戲開發 (Game Dev)')),
                                      DropdownMenuItem(value: 'JadeTrading', child: Text('💎 玉石交易 (Jade Trading)')),
                                      DropdownMenuItem(value: 'Medical', child: Text('🏥 醫療系統 (Medical)')),
                                    ],
                                    onChanged: _isRunning ? null : (value) {
                                      if (value != null) {
                                        setState(() {
                                          _domain = value;
                                        });
                                      }
                                    },
                                    dropdownColor: const Color(0xFF1F2937),
                                    style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 14),
                                    decoration: InputDecoration(
                                      filled: true,
                                      fillColor: const Color(0xFF1F2937),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      enabledBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      focusedBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF6366F1), width: 2),
                                      ),
                                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              // Language Selector
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    '語言設定 (Language)',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF6B7280),
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  DropdownButtonFormField<String>(
                                    initialValue: _language,
                                    items: const [
                                      DropdownMenuItem(value: 'zh-Hant', child: Text('🇹🇼 繁體中文 (Traditional Chinese)')),
                                      DropdownMenuItem(value: 'en', child: Text('🇺🇸 English')),
                                    ],
                                    onChanged: _isRunning ? null : (value) {
                                      if (value != null) {
                                        setState(() {
                                          _language = value;
                                        });
                                      }
                                    },
                                    dropdownColor: const Color(0xFF1F2937),
                                    style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 14),
                                    decoration: InputDecoration(
                                      filled: true,
                                      fillColor: const Color(0xFF1F2937),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      enabledBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      focusedBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF6366F1), width: 2),
                                      ),
                                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              // LLM Profile Selector
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'LLM 模型 (LLM Profile)',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF6B7280),
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  DropdownButtonFormField<String>(
                                    initialValue: _selectedLlmProfile.isNotEmpty ? _selectedLlmProfile : null,
                                    items: _llmProfiles.map((profileName) =>
                                      DropdownMenuItem(value: profileName, child: Text(profileName))
                                    ).toList(),
                                    onChanged: _isRunning ? null : (value) {
                                      if (value != null) {
                                        setState(() {
                                          _selectedLlmProfile = value;
                                        });
                                      }
                                    },
                                    dropdownColor: const Color(0xFF1F2937),
                                    style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 14),
                                    decoration: InputDecoration(
                                      filled: true,
                                      fillColor: const Color(0xFF1F2937),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      enabledBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      focusedBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF6366F1), width: 2),
                                      ),
                                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              // Task Input
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    '開發任務 (Task)',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF6B7280),
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  TextField(
                                    controller: TextEditingController(text: _task),
                                    onChanged: (value) {
                                      setState(() {
                                        _task = value;
                                      });
                                    },
                                    enabled: !_isRunning,
                                    maxLines: 5,
                                    style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 14),
                                    decoration: InputDecoration(
                                      filled: true,
                                      fillColor: const Color(0xFF1F2937),
                                      hintText: '請描述您想開發的軟體...',
                                      hintStyle: const TextStyle(color: Color(0xFF6B7280)),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      enabledBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF374151)),
                                      ),
                                      focusedBorder: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(8.0),
                                        borderSide: const BorderSide(color: Color(0xFF6366F1), width: 2),
                                      ),
                                      contentPadding: const EdgeInsets.all(12),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 24),
                              // Actions (Start/Stop)
                              Row(
                                children: [
                                  Expanded(
                                    child: ElevatedButton.icon(
                                      onPressed: _isRunning || _selectedLlmProfile.isEmpty ? null : _startWorkflow,
                                      icon: const Icon(Icons.play_arrow, size: 16),
                                      label: const Text('開始開發 (Start)'),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: const Color(0xFF4F46E5),
                                        foregroundColor: Colors.white,
                                        padding: const EdgeInsets.symmetric(vertical: 12),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(8.0),
                                        ),
                                        textStyle: const TextStyle(fontWeight: FontWeight.bold),
                                        elevation: 5,
                                        shadowColor: const Color.fromRGBO(79, 70, 229, 0.2),
                                      ).copyWith(
                                        backgroundColor: WidgetStateProperty.resolveWith<Color?>(
                                          (Set<WidgetState> states) {
                                            if (states.contains(WidgetState.disabled)) {
                                              return const Color(0xFF4B5563);
                                            }
                                            return const Color(0xFF4F46E5);
                                          },
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: ElevatedButton.icon(
                                      onPressed: !_isRunning ? null : _stopWorkflow,
                                      icon: const Icon(Icons.stop, size: 16),
                                      label: const Text('停止 (Stop)'),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: const Color(0xFFDC2626),
                                        foregroundColor: Colors.white,
                                        padding: const EdgeInsets.symmetric(vertical: 12),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(8.0),
                                        ),
                                        textStyle: const TextStyle(fontWeight: FontWeight.bold),
                                        elevation: 5,
                                        shadowColor: const Color.fromRGBO(220, 38, 38, 0.2),
                                      ).copyWith(
                                        backgroundColor: WidgetStateProperty.resolveWith<Color?>(
                                          (Set<WidgetState> states) {
                                            if (states.contains(WidgetState.disabled)) {
                                              return const Color(0xFF4B5563);
                                            }
                                            return const Color(0xFFDC2626);
                                          },
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                
                // Footer (Fixed at bottom)
                Container(
                  padding: const EdgeInsets.all(16.0),
                  color: const Color.fromRGBO(0, 0, 0, 0.2),
                  width: double.infinity, // Ensure it takes full width
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: _isOllamaRunning ? Colors.green : Colors.red,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _isOllamaRunning ? 'Ollama Online ($_ollamaVersion)' : 'Ollama Offline',
                            style: TextStyle(
                              fontSize: 11,
                              color: _isOllamaRunning ? Colors.green[200] : Colors.red[200],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Powered by PyMaestro API | ChatDev-X',
                        style: TextStyle(
                          fontSize: 10,
                          color: Color(0xFF6B7280),
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // Main Content Area
          Expanded(
            child: Column(
              children: [
                // Header (Phase Indicator)
                Container(
                  height: 64, // h-16
                  decoration: const BoxDecoration(
                    border: Border(bottom: BorderSide(color: Color(0xFF374151))), // border-b border-gray-800
                    color: Color(0xFF171717), // bg-gray-900/80 (approximated)
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 32.0), // px-8
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Text(
                            '目前階段 (Phase):',
                            style: TextStyle(
                              fontSize: 14, // text-sm
                              fontWeight: FontWeight.w500, // font-medium
                              color: Color(0xFF9CA3AF), // text-gray-400
                            ),
                          ),
                          const SizedBox(width: 16), // gap-4
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4), // px-3 py-1
                            decoration: BoxDecoration(
                              color: const Color(0xFF1A202C), // bg-indigo-900/30 (placeholder)
                              borderRadius: BorderRadius.circular(999), // rounded-full
                              border: Border.all(color: const Color(0xFF374151)), // border-indigo-800
                            ),
                            child: Text(
                              _currentPhase, // Dynamic Phase
                              style: const TextStyle(
                                fontSize: 12, // text-xs
                                fontWeight: FontWeight.bold, // font-bold
                                color: Color(0xFF6366F1), // text-indigo-400
                              ),
                            ),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          Icon(Icons.settings_input_component, size: 14, color: Color(0xFF9CA3AF)), // cpu icon
                          SizedBox(width: 4),
                          Text('${_currentSteps} Steps', style: TextStyle(fontSize: 12, color: Color(0xFF9CA3AF))), // Dynamic Steps
                          SizedBox(width: 16), // gap-4
                          Icon(Icons.code, size: 14, color: Color(0xFF9CA3AF)), // code icon
                          SizedBox(width: 4),
                          Text('${_currentLoc} LOC', style: TextStyle(fontSize: 12, color: Color(0xFF9CA3AF))), // Dynamic LOC
                        ],
                      ),
                    ],
                  ),
                ),
                // Active Agents Visualization
                Container(
                  height: 192, // h-48
                  decoration: const BoxDecoration(
                    border: Border(bottom: BorderSide(color: Color(0xFF374151))), // border-b border-gray-800
                    color: Color(0xFF1A202C), // bg-gray-900/30
                  ),
                  child: Center(
                    child: SingleChildScrollView( // Added SingleChildScrollView
                      scrollDirection: Axis.horizontal, // To allow horizontal scrolling if many agents
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: _agents.map((agent) => Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12.0), // Equivalent to gap-6
                          child: AgentCard(
                            name: agent.displayName, // Use displayName from backend
                            role: agent.description, // Use description from backend
                            icon: agent.icon,
                            color: agent.color,
                            isActive: _activeAgentName == agent.name, // Compare with agent.name
                          ),
                        )).toList(),
                      ),
                    ),
                  ),
                ),
                // Main Content Area
                Expanded(
                  child: Stack(
                    children: [
                      Center(
                        child: _renderContent(), // Placeholder for content based on currentPage
                      ),
                      if (_isRunning) // Conditionally show loading indicator
                        Positioned(
                          bottom: 16, // Equivalent to bottom-4
                          left: 0,
                          right: 0,
                          child: Center(
                            child: const LoadingIndicator(),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContentPage(IconData icon, String title, String description) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(icon, size: 48, color: Colors.white70),
        const SizedBox(height: 16),
        Text(
          title,
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: Colors.white),
        ),
        const SizedBox(height: 8),
        Text(
          description,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white54),
        ),
      ],
    );
  }

  Widget _buildNavItem(String page, IconData icon, String text, {bool hasBadge = false}) {
    return InkWell(
      onTap: () {
        setState(() {
          _currentPage = page;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8), // px-4 py-2
        decoration: BoxDecoration(
          color: _currentPage == page
              ? const Color(0xFF4F46E5) // bg-indigo-600
              : Colors.transparent,
          borderRadius: BorderRadius.circular(8.0), // rounded-lg
        ),
        child: Row(
          children: [
            Icon(icon, size: 16, color: _currentPage == page ? Colors.white : const Color(0xFFD1D5DB)), // text-gray-300
            const SizedBox(width: 8), // gap-2
            Text(
              text,
              style: TextStyle(
                fontWeight: FontWeight.w500, // font-medium
                color: _currentPage == page ? Colors.white : const Color(0xFFD1D5DB),
              ),
            ),
            if (hasBadge) // Placeholder for badge (e.g., for Approvals)
              const Spacer(),
              if (hasBadge)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2), // px-2 py-0.5
                  decoration: BoxDecoration(
                    color: const Color(0xFFEA580C), // bg-orange-700
                    borderRadius: BorderRadius.circular(999), // rounded-full
                  ),
                  child: const Text(
                    '0', // Placeholder count
                    style: TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.w600), // text-xs font-semibold
                  ),
                ),
          ],
        ),
      ),
    );
  }

  // Function to save Global Config to the FastAPI backend
  Future<void> _saveConfig() async {
    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:8000/config'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'ollama_host': _ollamaHostController.text,
          'max_iterations': int.tryParse(_maxIterationsController.text) ?? 5, // Default to 5 if parsing fails
          'enable_sandbox': _enableSandbox,
          'human_approval': _humanApproval,
        }),
      );

      if (response.statusCode == 200) {
        print('Config saved successfully: ${response.body}');
        _fetchConfig(); // Re-fetch to ensure UI consistency
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Global settings saved successfully!')),
        );
      } else {
        final errorData = json.decode(response.body);
        print('Failed to save config: ${response.statusCode} - ${errorData['detail']}');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to save settings: ${errorData['detail']}')),
        );
      }
    } catch (e) {
      print('Error saving config: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error saving settings: $e')),
      );
    }
  }

  // Function to fetch past workflow runs
  Future<List<Map<String, String>>> _fetchPastWorkflows() async {
    try {
      final response = await http.get(Uri.parse('http://127.0.0.1:8000/workflow/runs'));
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> runsJson = data['runs'];
        return runsJson.map((run) => {
          'run_id': run['run_id'] as String,
          'timestamp': run['timestamp'] as String? ?? 'N/A',
          'user_prompt': run['user_prompt'] as String? ?? 'No prompt recorded',
        }).toList();
      } else {
        print('Failed to load past workflows: ${response.statusCode}');
        return Future.error('Failed to load past workflows: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching past workflows: $e');
      return Future.error('Error fetching past workflows: $e');
    }
  }

  Widget _renderContent() {
    switch (_currentPage) {
      case 'new-workflow':
        return ChatLog(messages: _messages, scrollController: _scrollController);
      case 'workflow-status':
        return _buildWorkflowStatusContent();
      case 'pending-approvals':
        return _buildContentPage(Icons.settings_input_component, '審核 (Approvals)', '這裡將顯示需要人工審核的步驟，等待您的決策。');
      case 'llm-profiles':
        return _buildLlmProfilesContent();
      case 'settings':
        return _buildGlobalSettingsContent();
      case 'past-workflows':
        return _buildPastWorkflowsContent();
      case 'welcome':
      default:
        return Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFF1F2937),
                borderRadius: BorderRadius.circular(16.0),
              ),
              child: Icon(Icons.dashboard, size: 40, color: const Color.fromARGB(128, 255, 255, 255)),
            ),
            const SizedBox(height: 16),
            const Text(
              '歡迎使用 ChatDev-X！請從左側導航欄選擇一個選項來開始。',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFF9CA3AF)),
            ),
          ],
        );
    }
  }

  Widget _buildWorkflowStatusContent() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '執行狀態 (Workflow Status)',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          Card(
            color: const Color(0xFF1F2937),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.info, color: Colors.blue),
                      const SizedBox(width: 8),
                      Text('Current Phase: $_currentPhase', style: TextStyle(color: Colors.white)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.timeline, color: Colors.green),
                      const SizedBox(width: 8),
                      Text('Steps Completed: $_currentSteps', style: TextStyle(color: Colors.white)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.code, color: Colors.orange),
                      const SizedBox(width: 8),
                      Text('Lines of Code: $_currentLoc', style: TextStyle(color: Colors.white)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.person, color: Colors.purple),
                      const SizedBox(width: 8),
                      Text('Active Agent: $_activeAgentName', style: TextStyle(color: Colors.white)),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLlmProfilesContent() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'LLM 設定 (LLM Profiles)',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              ElevatedButton.icon(
                onPressed: _showAddProfileDialog,
                icon: Icon(Icons.add),
                label: Text('Add Profile'),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4F46E5)),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: _llmProfiles.length,
              itemBuilder: (context, index) {
                final profile = _llmProfiles[index];
                return Card(
                  color: const Color(0xFF1F2937),
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: Icon(Icons.settings_applications, color: Colors.blue),
                    title: Text(profile, style: TextStyle(color: Colors.white)),
                    trailing: IconButton(
                      icon: Icon(Icons.delete, color: Colors.red),
                      onPressed: () => _deleteProfile(profile),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGlobalSettingsContent() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '全局設定 (Global Settings)',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                children: [
                  Card(
                    color: const Color(0xFF1F2937),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Ollama Host', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          TextField(
                            controller: _ollamaHostController,
                            style: TextStyle(color: Colors.white),
                            decoration: InputDecoration(
                              filled: true,
                              fillColor: const Color(0xFF374151),
                              border: OutlineInputBorder(),
                              hintText: 'http://localhost:11434',
                              hintStyle: TextStyle(color: Colors.grey),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Text('Max Iterations', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          TextField(
                            controller: _maxIterationsController,
                            style: TextStyle(color: Colors.white),
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              filled: true,
                              fillColor: const Color(0xFF374151),
                              border: OutlineInputBorder(),
                              hintText: '5',
                              hintStyle: TextStyle(color: Colors.grey),
                            ),
                          ),
                          const SizedBox(height: 16),
                          SwitchListTile(
                            title: Text('Enable Sandbox', style: TextStyle(color: Colors.white)),
                            value: _enableSandbox,
                            onChanged: (value) => setState(() => _enableSandbox = value),
                            activeColor: const Color(0xFF4F46E5),
                          ),
                          SwitchListTile(
                            title: Text('Human Approval', style: TextStyle(color: Colors.white)),
                            value: _humanApproval,
                            onChanged: (value) => setState(() => _humanApproval = value),
                            activeColor: const Color(0xFF4F46E5),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: _saveConfig,
                            child: Text('Save Settings'),
                            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4F46E5)),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPastWorkflowsContent() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '歷史任務 (Past Tasks)',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: FutureBuilder<List<Map<String, String>>>(
              future: _fetchPastWorkflows(),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return Center(child: CircularProgressIndicator());
                } else if (snapshot.hasError) {
                  return Center(
                    child: Text(
                      'Error: ${snapshot.error}',
                      style: TextStyle(color: Colors.red),
                    ),
                  );
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return Center(
                    child: Text(
                      'No past workflows found.',
                      style: TextStyle(color: Colors.grey),
                    ),
                  );
                } else {
                  final workflows = snapshot.data!;
                  return ListView.builder(
                    itemCount: workflows.length,
                    itemBuilder: (context, index) {
                      final workflow = workflows[index];
                      return Card(
                        color: const Color(0xFF1F2937),
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: Icon(Icons.history, color: Colors.blue),
                          title: Text(
                            workflow['run_id']!,
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                workflow['user_prompt']!,
                                style: TextStyle(color: Colors.grey),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              Text(
                                workflow['timestamp']!,
                                style: TextStyle(color: Colors.grey, fontSize: 12),
                              ),
                            ],
                          ),
                          isThreeLine: true,
                        ),
                      );
                    },
                  );
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  void _showAddProfileDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1F2937),
        title: Text('Add LLM Profile', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _profileNameController,
              style: TextStyle(color: Colors.white),
              decoration: InputDecoration(
                labelText: 'Profile Name',
                labelStyle: TextStyle(color: Colors.grey),
                filled: true,
                fillColor: const Color(0xFF374151),
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _modelIdController,
              style: TextStyle(color: Colors.white),
              decoration: InputDecoration(
                labelText: 'Model ID',
                labelStyle: TextStyle(color: Colors.grey),
                filled: true,
                fillColor: const Color(0xFF374151),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: _addProfile,
            child: Text('Add'),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4F46E5)),
          ),
        ],
      ),
    );
  }

  Future<void> _addProfile() async {
    final name = _profileNameController.text.trim();
    final modelId = _modelIdController.text.trim();
    
    if (name.isEmpty || modelId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please fill all fields')),
      );
      return;
    }

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:8000/profiles'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'name': name,
          'config': {
            'product_manager': {
              'name': 'PM Model',
              'model_id': modelId,
              'role': 'product_manager',
            },
          },
        }),
      );

      if (response.statusCode == 200) {
        Navigator.pop(context);
        _profileNameController.clear();
        _modelIdController.clear();
        _fetchLlmProfiles();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Profile added successfully!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to add profile')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  Future<void> _deleteProfile(String profileName) async {
    try {
      final response = await http.delete(
        Uri.parse('http://127.0.0.1:8000/profiles/$profileName'),
      );

      if (response.statusCode == 200) {
        _fetchLlmProfiles();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Profile deleted successfully!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to delete profile')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  void _showErrorDialog(String title, String content) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1F2937),
        title: Text(title, style: const TextStyle(color: Colors.white)),
        content: Text(content, style: const TextStyle(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }
}