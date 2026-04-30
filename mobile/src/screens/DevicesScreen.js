import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useNetwork } from '../context/NetworkContext';
import api from '../config/api';
import DeviceCard from '../components/DeviceCard';
import { colors } from '../theme';
import { getDevicesOffline, saveDevicesOffline } from '../utils/storage';

export default function DevicesScreen({ navigation }) {
  const { isConnected } = useNetwork();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    if (!isConnected) {
      // Load from offline storage
      const offlineDevices = await getDevicesOffline();
      setDevices(offlineDevices);
      setLoading(false);
      setRefreshing(false);
      return;
    }

    try {
      const response = await api.get('/api/devices');
      const devicesData = response.data.devices || [];
      setDevices(devicesData);
      // Save to offline storage
      await saveDevicesOffline(devicesData);
    } catch (error) {
      console.error('Error loading devices:', error);
      // Fallback to offline data
      const offlineDevices = await getDevicesOffline();
      setDevices(offlineDevices);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadDevices();
  };

  if (loading && devices.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!isConnected) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.offlineText}>No Internet Connection</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={devices}
        keyExtractor={(item, index) =>
          String(
            item.id ||
              item._id ||
              item.device_id ||
              item.deviceId ||
              `device-${index}`
          )
        }
        renderItem={({ item }) => (
          <DeviceCard device={item} navigation={navigation} />
        )}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No devices yet</Text>
            <TouchableOpacity style={styles.addButton}>
              <Text style={styles.addButtonText}>Add Device</Text>
            </TouchableOpacity>
          </View>
        }
        contentContainerStyle={styles.listContent}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.bg,
  },
  offlineText: {
    fontSize: 16,
    color: colors.muted,
  },
  listContent: {
    paddingVertical: 16,
  },
  emptyState: {
    padding: 48,
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
