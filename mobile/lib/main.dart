import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/home/home_screen.dart';
import 'services/device_service.dart';
import 'services/websocket_service.dart';

void main() {
  runApp(const AgentLinkerApp());
}

class AgentLinkerApp extends StatelessWidget {
  const AgentLinkerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => DeviceService()),
        ChangeNotifierProvider(create: (_) => WebSocketService()),
      ],
      child: MaterialApp(
        title: 'AgentLinker',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.blue,
            brightness: Brightness.light,
          ),
          useMaterial3: true,
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.blue,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
        ),
        themeMode: ThemeMode.system,
        home: const HomeScreen(),
      ),
    );
  }
}
