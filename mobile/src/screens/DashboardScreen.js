import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { useNetwork } from '../context/NetworkContext';
import api from '../config/api';
import DeviceCard from '../components/DeviceCard';
import AlertCard from '../components/AlertCard';
import StatsCard from '../components/StatsCard';
import { colors } from '../theme';
import { initializeRealtime, disconnectRealtime } from '../services/realtime';
import { getDevicesOffline, getAlertsOffline, saveDevicesOffline, saveAlertsOffline } from '../utils/storage';

export default function DashboardScreen({ navigation }) {
  const { user } = useAuth();
  const { isConnected } = useNetwork();
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    totalDevices: 0,
    onlineDevices: 0,
    totalAlerts: 0,
    criticalAlerts: 0,
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Initialize real-time updates when user is available
  useEffect(() => {
    if (!user) return;

    initializeRealtime(user, {
      onDeviceUpdate: () => {
        // Refresh dashboard data when devices change
        loadData();
      },
      onNewAlert: () => {
        // Refresh dashboard data when new alerts arrive
        loadData();
      },
      onAlertResolved: () => {
        // Refresh dashboard data when alerts are resolved
        loadData();
      },
    });

    return () => {
      disconnectRealtime();
    };
  }, [user]);

  const loadData = async () => {
    if (!isConnected) {
      // Load from offline storage
      const offlineDevices = await getDevicesOffline();
      const offlineAlerts = await getAlertsOffline();
      setDevices(offlineDevices.slice(0, 5));
      setAlerts(offlineAlerts.filter(a => !a.resolved).slice(0, 5));
      setLoading(false);
      setRefreshing(false);
      return;
    }

    try {
      const [devicesRes, alertsRes, analyticsRes] = await Promise.allSettled([
        api.get('/api/devices', { params: { page: 1, limit: 5 } }),
        api.get('/api/alerts', { params: { page: 1, limit: 5, resolved: false } }),
        api.get('/api/analytics/devices/stats'),
      ]);

      const devicesData =
        devicesRes.status === 'fulfilled' ? devicesRes.value.data.devices || [] : [];
      const alertsData =
        alertsRes.status === 'fulfilled' ? alertsRes.value.data.alerts || [] : [];

      setDevices(devicesData);
      setAlerts(alertsData);

      await saveDevicesOffline(devicesData);
      await saveAlertsOffline(alertsData);

      const totalAlertsCount =
        alertsRes.status === 'fulfilled' ? alertsRes.value.data.total || 0 : 0;
      const criticalOnPage = alertsData.filter((a) => a.severity === 'critical').length;

      if (analyticsRes.status === 'fulfilled' && analyticsRes.value.data) {
        const d = analyticsRes.value.data;
        const breakdown = d.status_breakdown || {};
        setStats({
          totalDevices: d.total_devices || 0,
          onlineDevices: breakdown.online || 0,
          totalAlerts: totalAlertsCount,
          criticalAlerts: criticalOnPage,
        });
      } else if (alertsRes.status === 'fulfilled') {
        setStats((s) => ({
          ...s,
          totalAlerts: totalAlertsCount,
          criticalAlerts: criticalOnPage,
        }));
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Fallback to offline data
      const offlineDevices = await getDevicesOffline();
      const offlineAlerts = await getAlertsOffline();
      setDevices(offlineDevices.slice(0, 5));
      setAlerts(offlineAlerts.filter(a => !a.resolved).slice(0, 5));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (!isConnected) {
    return (
      <View style={styles.offlineContainer}>
        <Text style={styles.offlineText}>No Internet Connection</Text>
        <Text style={styles.offlineSubtext}>Please check your connection and try again</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome back, {user?.name || 'User'}!</Text>
        <Text style={styles.subtitle}>Here's your security overview</Text>
      </View>

      <View style={styles.statsContainer}>
        <StatsCard
          title="Devices"
          value={stats.onlineDevices}
          subtitle={`${stats.totalDevices} total`}
          color={colors.primary}
        />
        <StatsCard
          title="Alerts"
          value={stats.totalAlerts}
          subtitle={`${stats.criticalAlerts} critical`}
          color={stats.criticalAlerts > 0 ? colors.danger : colors.ok}
        />
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Devices</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Devices')}>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        </View>
        {devices.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No devices yet</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => navigation.navigate('Devices')}
            >
              <Text style={styles.addButtonText}>Add Device</Text>
            </TouchableOpacity>
          </View>
        ) : (
          devices.map((device) => (
            <DeviceCard key={device.id} device={device} navigation={navigation} />
          ))
        )}
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Active Alerts</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Alerts')}>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        </View>
        {alerts.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No active alerts</Text>
          </View>
        ) : (
          alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} navigation={navigation} />
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  offlineContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.bg,
    padding: 24,
  },
  offlineText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 8,
  },
  offlineSubtext: {
    fontSize: 14,
    color: colors.muted,
    textAlign: 'center',
  },
  header: {
    padding: 24,
    paddingTop: 16,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: colors.muted,
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 24,
    marginBottom: 24,
    gap: 16,
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  seeAll: {
    fontSize: 14,
    color: colors.primary,
  },
  emptyState: {
    padding: 24,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: colors.muted,
    marginBottom: 16,
  },
  addButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
});
