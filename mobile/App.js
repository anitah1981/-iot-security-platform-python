import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { NetworkProvider } from './src/context/NetworkContext';
import { registerForPushNotifications } from './src/services/notifications';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import SignupScreen from './src/screens/SignupScreen';
import ForgotPasswordScreen from './src/screens/ForgotPasswordScreen';
import ResetPasswordScreen from './src/screens/ResetPasswordScreen';
import DeviceDetailScreen from './src/screens/DeviceDetailScreen';
import AlertDetailScreen from './src/screens/AlertDetailScreen';
import MainTabs from './src/navigation/MainTabs';
import LoadingScreen from './src/screens/LoadingScreen';

const Stack = createNativeStackNavigator();

function AuthNavigator() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: '#1a1a1a' },
          headerTintColor: '#ffffff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      >
        {user ? (
          <>
            <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
            <Stack.Screen
              name="DeviceDetail"
              component={DeviceDetailScreen}
              options={{ title: 'Device Details' }}
            />
            <Stack.Screen
              name="AlertDetail"
              component={AlertDetailScreen}
              options={{ title: 'Alert Details' }}
            />
          </>
        ) : (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Signup" component={SignupScreen} />
            <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
            <Stack.Screen name="ResetPassword" component={ResetPasswordScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  useEffect(() => {
    // Register for push notifications on app start
    registerForPushNotifications().then((token) => {
      if (token) {
        console.log('Push notification token:', token);
        // TODO: Send token to your backend API
      }
    });
  }, []);

  return (
    <NetworkProvider>
      <AuthProvider>
        <StatusBar style="light" />
        <AuthNavigator />
      </AuthProvider>
    </NetworkProvider>
  );
}
