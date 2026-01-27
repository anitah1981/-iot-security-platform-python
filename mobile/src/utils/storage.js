// Offline storage utilities
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEYS = {
  DEVICES: '@devices_cache',
  ALERTS: '@alerts_cache',
  LAST_SYNC: '@last_sync',
};

export async function saveDevicesOffline(devices) {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.DEVICES, JSON.stringify(devices));
    await AsyncStorage.setItem(STORAGE_KEYS.LAST_SYNC, new Date().toISOString());
  } catch (error) {
    console.error('Error saving devices offline:', error);
  }
}

export async function getDevicesOffline() {
  try {
    const data = await AsyncStorage.getItem(STORAGE_KEYS.DEVICES);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Error getting devices offline:', error);
    return [];
  }
}

export async function saveAlertsOffline(alerts) {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.ALERTS, JSON.stringify(alerts));
  } catch (error) {
    console.error('Error saving alerts offline:', error);
  }
}

export async function getAlertsOffline() {
  try {
    const data = await AsyncStorage.getItem(STORAGE_KEYS.ALERTS);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Error getting alerts offline:', error);
    return [];
  }
}

export async function getLastSyncTime() {
  try {
    const time = await AsyncStorage.getItem(STORAGE_KEYS.LAST_SYNC);
    return time ? new Date(time) : null;
  } catch (error) {
    console.error('Error getting last sync time:', error);
    return null;
  }
}
