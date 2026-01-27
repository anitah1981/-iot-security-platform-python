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
      const [devicesRes, alertsRes, analyticsRes] = await Promise.all([
        api.get('/api/devices?limit=5'),
        api.get('/api/alerts?limit=5&resolved=false'),
        api.get('/api/analytics/stats'),
      ]);

      const devicesData = devicesRes.data.devices || [];
      const alertsData = alertsRes.data.alerts || [];

      setDevices(devicesData);
      setAlerts(alertsData);
      
      // Save to offline storage
      await saveDevicesOffline(devicesData);
      await saveAlertsOffline(alertsData);
      
      if (analyticsRes.data) {
        setStats({
          totalDevices: analyticsRes.data.total_devices || 0,
          onlineDevices: analyticsRes.data.online_devices || 0,
          totalAlerts: analyticsRes.data.total_alerts || 0,
          criticalAlerts: analyticsRes.data.critical_alerts || 0,
        });
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
          color="#3b82f6"
        />
        <StatsCard
          title="Alerts"
          value={stats.totalAlerts}
          subtitle={`${stats.criticalAlerts} critical`}
          color={stats.criticalAlerts > 0 ? '#ef4444' : '#10b981'}
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
    backgroundColor: '#1a1a1a',
  },
  offlineContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    padding: 24,
  },
  offlineText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  offlineSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  header: {
    padding: 24,
    paddingTop: 16,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#999',
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
    color: '#ffffff',
  },
  seeAll: {
    fontSize: 14,
    color: '#3b82f6',
  },
  emptyState: {
    padding: 24,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    marginBottom: 16,
  },
  addButton: {
    backgroundColor: '#3b82f6',
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
