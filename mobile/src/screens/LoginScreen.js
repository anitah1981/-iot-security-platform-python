import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  Image,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { colors, borderRadius } from '../theme';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [showMfa, setShowMfa] = useState(false);
  const [loading, setLoading] = useState(false);
  const [connectionChecking, setConnectionChecking] = useState(false);
  const [serverUrlInput, setServerUrlInput] = useState('');
  const [savingUrl, setSavingUrl] = useState(false);
  const { login, checkConnection, setApiUrlOverride, apiUrl } = useAuth();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password');
      return;
    }
    if (showMfa && !mfaCode.trim()) {
      Alert.alert('Error', 'Enter the 6-digit code from your authenticator app');
      return;
    }

    setLoading(true);
    const result = await login(
      email.toLowerCase().trim(),
      password,
      showMfa ? mfaCode.trim() : null
    );
    setLoading(false);

    if (result.success) return;
    if (result.mfaRequired) {
      setShowMfa(true);
      return;
    }
    Alert.alert('Login Failed', result.error || 'Invalid credentials');
  };

  const handleCheckConnection = async () => {
    setConnectionChecking(true);
    const result = await checkConnection();
    setConnectionChecking(false);
    if (result.ok) {
      Alert.alert('Connection OK', `Server at ${apiUrl} is reachable.`);
    } else {
      Alert.alert('Connection Failed', (result.error || 'Unknown error') + (result.apiUrl ? `\n\nApp is using: ${result.apiUrl}` : ''));
    }
  };

  const handleSetServerUrl = async () => {
    const url = serverUrlInput.trim();
    if (!url) {
      Alert.alert('Error', 'Enter a server URL (e.g. https://xxx.up.railway.app)');
      return;
    }
    setSavingUrl(true);
    try {
      await setApiUrlOverride(url);
      Alert.alert('Server URL updated', `Using: ${url}\n\nTap "Check connection" to verify.`);
    } catch (e) {
      Alert.alert('Error', e?.message || 'Failed to update URL');
    }
    setSavingUrl(false);
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.content}>
        <View style={styles.logoContainer}>
          <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
        </View>
        <Text style={styles.title}>Pro-Alert</Text>
        <Text style={styles.subtitle}>Sign in to access your devices and alerts</Text>

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={colors.muted}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
          />

          <TextInput
            style={styles.input}
            placeholder="Password"
            placeholderTextColor={colors.muted}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
            autoComplete="password"
          />

          {showMfa && (
            <>
              <Text style={styles.mfaLabel}>MFA Code</Text>
              <TextInput
                style={styles.input}
                placeholder="000000"
                placeholderTextColor={colors.muted}
                value={mfaCode}
                onChangeText={setMfaCode}
                keyboardType="number-pad"
                maxLength={6}
                autoComplete="one-time-code"
              />
              <Text style={styles.mfaHint}>Enter the 6-digit code from your authenticator app</Text>
            </>
          )}

          <TouchableOpacity
            style={styles.forgotPassword}
            onPress={() => navigation.navigate('ForgotPassword')}
          >
            <Text style={styles.forgotPasswordText}>Forgot password?</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.buttonText}>Sign In</Text>
            )}
          </TouchableOpacity>

          <View style={styles.signupContainer}>
            <Text style={styles.signupText}>Don't have an account? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Signup')}>
              <Text style={styles.signupLink}>Sign Up</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.serverUrl}>Server: {apiUrl || '…'}</Text>
          <TouchableOpacity
            style={styles.linkButton}
            onPress={handleCheckConnection}
            disabled={connectionChecking}
          >
            <Text style={styles.linkButtonText}>
              {connectionChecking ? 'Checking…' : 'Check connection'}
            </Text>
          </TouchableOpacity>

          <Text style={styles.overrideLabel}>Not working? Enter your Railway URL and tap Use:</Text>
          <TextInput
            style={[styles.input, styles.serverInput]}
            placeholder="https://xxx.up.railway.app"
            placeholderTextColor={colors.muted}
            value={serverUrlInput}
            onChangeText={setServerUrlInput}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
          <TouchableOpacity
            style={[styles.linkButton, styles.useServerButton]}
            onPress={handleSetServerUrl}
            disabled={savingUrl}
          >
            <Text style={styles.linkButtonText}>{savingUrl ? 'Saving…' : 'Use this server'}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  logo: {
    height: 80,
    width: 180,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: colors.muted,
    textAlign: 'center',
    marginBottom: 32,
  },
  form: {
    width: '100%',
  },
  input: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.md,
    padding: 16,
    color: colors.text,
    fontSize: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  mfaLabel: {
    color: colors.muted,
    fontSize: 14,
    marginTop: 8,
    marginBottom: 4,
  },
  mfaHint: {
    color: colors.muted,
    fontSize: 12,
    marginBottom: 16,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  forgotPasswordText: {
    color: colors.primary,
    fontSize: 14,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    padding: 16,
    alignItems: 'center',
    marginBottom: 16,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  signupContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 16,
  },
  signupText: {
    color: colors.muted,
    fontSize: 14,
  },
  signupLink: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  serverUrl: {
    color: colors.muted,
    fontSize: 11,
    marginTop: 16,
    textAlign: 'center',
  },
  linkButton: {
    marginTop: 8,
    padding: 8,
    alignItems: 'center',
  },
  linkButtonText: {
    color: colors.muted,
    fontSize: 13,
  },
  overrideLabel: {
    color: colors.muted,
    fontSize: 12,
    marginTop: 20,
    marginBottom: 6,
  },
  serverInput: {
    fontSize: 13,
    marginBottom: 8,
  },
  useServerButton: {
    marginBottom: 24,
  },
});
