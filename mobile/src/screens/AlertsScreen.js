import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useNetwork } from '../context/NetworkContext';
import api from '../config/api';
import AlertCard from '../components/AlertCard';
import { getAlertsOffline, saveAlertsOffline } from '../utils/storage';

export default function AlertsScreen({ navigation }) {
  const { isConnected } = useNetwork();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all'); // all, unresolved, critical

  useEffect(() => {
    loadAlerts();
  }, [filter]);

  const loadAlerts = async () => {
    if (!isConnected) {
      // Load from offline storage
      const offlineAlerts = await getAlertsOffline();
      let filtered = offlineAlerts;
      if (filter === 'unresolved') {
        filtered = offlineAlerts.filter(a => !a.resolved);
      } else if (filter === 'critical') {
        filtered = offlineAlerts.filter(a => a.severity === 'critical');
      }
      setAlerts(filtered);
      setLoading(false);
      setRefreshing(false);
      return;
    }

    try {
      const params = { limit: 50 };
      if (filter === 'unresolved') {
        params.resolved = false;
      } else if (filter === 'critical') {
        params.severity = 'critical';
      }

      const response = await api.get('/api/alerts', { params });
      const alertsData = response.data.alerts || [];
      setAlerts(alertsData);
      // Save to offline storage
      await saveAlertsOffline(alertsData);
    } catch (error) {
      console.error('Error loading alerts:', error);
      // Fallback to offline data
      const offlineAlerts = await getAlertsOffline();
      let filtered = offlineAlerts;
      if (filter === 'unresolved') {
        filtered = offlineAlerts.filter(a => !a.resolved);
      } else if (filter === 'critical') {
        filtered = offlineAlerts.filter(a => a.severity === 'critical');
      }
      setAlerts(filtered);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadAlerts();
  };

  if (loading && alerts.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
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
      <View style={styles.filters}>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'all' && styles.filterActive]}
          onPress={() => setFilter('all')}
        >
          <Text style={[styles.filterText, filter === 'all' && styles.filterTextActive]}>
            All
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'unresolved' && styles.filterActive]}
          onPress={() => setFilter('unresolved')}
        >
          <Text
            style={[styles.filterText, filter === 'unresolved' && styles.filterTextActive]}
          >
            Active
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'critical' && styles.filterActive]}
          onPress={() => setFilter('critical')}
        >
          <Text style={[styles.filterText, filter === 'critical' && styles.filterTextActive]}>
            Critical
          </Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={alerts}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <AlertCard alert={item} navigation={navigation} />
        )}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No alerts found</Text>
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
    backgroundColor: '#1a1a1a',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  offlineText: {
    fontSize: 16,
    color: '#999',
  },
  filters: {
    flexDirection: 'row',
    paddingHorizontal: 24,
    paddingVertical: 16,
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#2a2a2a',
    borderWidth: 1,
    borderColor: '#333',
  },
  filterActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  filterText: {
    color: '#999',
    fontSize: 14,
    fontWeight: '500',
  },
  filterTextActive: {
    color: '#ffffff',
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
    color: '#999',
  },
});
