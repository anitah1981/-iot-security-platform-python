import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  ScrollView,
} from 'react-native';
import { DrawerContentScrollView, DrawerItemList } from '@react-navigation/drawer';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { colors } from '../theme';

const DRAWER_ITEMS = [
  { name: 'Dashboard', icon: 'stats-chart', label: 'Dashboard' },
  { name: 'Devices', icon: 'hardware-chip', label: 'Devices' },
  { name: 'Alerts', icon: 'notifications', label: 'Alerts' },
  { name: 'Family', icon: 'people', label: 'Family' },
  { name: 'Settings', icon: 'settings', label: 'Settings' },
  { name: 'AuditLogs', icon: 'document-text', label: 'Audit Logs' },
  { name: 'Incidents', icon: 'search', label: 'Incidents' },
  { name: 'SecurityThreats', icon: 'shield', label: 'Security Threats' },
  { name: 'SecurityCompliance', icon: 'lock-closed', label: 'Security & Compliance' },
  { name: 'Pricing', icon: 'card', label: 'Pricing' },
];

export default function CustomDrawerContent(props) {
  const { user, logout } = useAuth();

  return (
    <View style={styles.container}>
      <DrawerContentScrollView
        {...props}
        contentContainerStyle={styles.scrollContent}
        style={styles.scroll}
      >
        <View style={styles.header}>
          <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
          <Text style={styles.title}>Pro-Alert</Text>
          <Text style={styles.user}>{user?.email || 'User'}</Text>
        </View>

        <View style={styles.navContainer}>
          {DRAWER_ITEMS.map((item) => {
            const state = props.state;
            const currentRoute = state.routes[state.index];
            const isFocused = currentRoute?.name === item.name;

            return (
              <TouchableOpacity
                key={item.name}
                style={[styles.navItem, isFocused && styles.navItemActive]}
                onPress={() => props.navigation.navigate(item.name)}
              >
                <Ionicons
                  name={isFocused ? item.icon : `${item.icon}-outline`}
                  size={22}
                  color={isFocused ? colors.primary : colors.muted}
                />
                <Text style={[styles.navLabel, isFocused && styles.navLabelActive]}>{item.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </DrawerContentScrollView>

      <View style={styles.footer}>
        <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
          <Ionicons name="log-out-outline" size={22} color={colors.danger} />
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 8,
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 24,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  logo: {
    height: 48,
    width: 120,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
  },
  user: {
    fontSize: 13,
    color: colors.muted,
    marginTop: 4,
  },
  navContainer: {
    paddingVertical: 16,
    paddingHorizontal: 12,
  },
  navItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 4,
    gap: 16,
  },
  navItemActive: {
    backgroundColor: colors.primary + '20',
  },
  navLabel: {
    fontSize: 16,
    color: colors.muted,
  },
  navLabelActive: {
    color: colors.primary,
    fontWeight: '600',
  },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: colors.danger + '15',
    gap: 12,
  },
  logoutText: {
    fontSize: 16,
    color: colors.danger,
    fontWeight: '600',
  },
});
