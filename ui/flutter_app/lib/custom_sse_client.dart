import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Represents a single Server-Sent Event (SSE) message.
class SseEvent {
  final String? id;
  final String? event;
  final String data;

  SseEvent({this.id, this.event, required this.data});

  @override
  String toString() {
    return 'SseEvent(id: $id, event: $event, data: $data)';
  }
}

/// A custom client for Server-Sent Events (SSE).
/// This client directly uses the `http` package for streaming and handles
/// the parsing of SSE formatted data.
class CustomSseClient {
  final String url;
  http.Client? _httpClient;
  StreamController<SseEvent>? _controller;
  StreamSubscription? _responseSubscription;

  CustomSseClient(this.url);

  /// Connects to the SSE endpoint and returns a stream of SseEvents.
  Stream<SseEvent> connect() {
    _controller = StreamController<SseEvent>(
      onListen: _startListening,
      onCancel: _stopListening,
    );
    return _controller!.stream;
  }

  void _startListening() async {
    _httpClient = http.Client();
    try {
      final request = http.Request('GET', Uri.parse(url));
      request.headers['Accept'] = 'text/event-stream';
      request.headers['Cache-Control'] = 'no-cache';

      final response = await _httpClient!.send(request);

      if (response.statusCode == 200) {
        String buffer = '';
        _responseSubscription = response.stream
            .transform(utf8.decoder)
            .listen(
          (chunk) {
            buffer += chunk;
            final lines = buffer.split('\n');
            buffer = lines.removeLast(); // Keep incomplete line in buffer

            for (var line in lines) {
              if (line.trim().isEmpty) {
                // End of an event
                _processBuffer(buffer);
                buffer = '';
              } else {
                buffer += '$line\n'; // Re-add newline for multi-line data parsing
              }
            }
          },
          onError: (error) {
            print('SSE Stream Error: $error');
            _controller?.addError(error);
            _stopListening();
          },
          onDone: () {
            print('SSE Stream Done.');
            _processBuffer(buffer); // Process any remaining data
            _controller?.close();
            _stopListening();
          },
        );
      } else {
        final error = 'Failed to connect to SSE: HTTP ${response.statusCode}';
        print(error);
        _controller?.addError(error);
        _controller?.close();
        _stopListening();
      }
    } catch (e) {
      print('Error connecting to SSE: $e');
      _controller?.addError(e);
      _controller?.close();
      _stopListening();
    }
  }

  void _processBuffer(String buffer) {
    if (buffer.trim().isEmpty) return;

    String? id;
    String? event;
    String data = '';

    final lines = buffer.split('\n');
    for (var line in lines) {
      if (line.startsWith('id:')) {
        id = line.substring(3).trim();
      } else if (line.startsWith('event:')) {
        event = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        // Concatenate data lines, removing leading 'data:'
        data += line.substring(5).trim();
      }
    }
    _controller?.add(SseEvent(id: id, event: event, data: data));
  }


  void _stopListening() {
    _responseSubscription?.cancel();
    _responseSubscription = null;
    _httpClient?.close();
    _httpClient = null;
    if (_controller != null && !_controller!.isClosed) {
      _controller?.close();
    }
  }

  void close() {
    _stopListening();
  }
}
