import React, { useState } from 'react';
import { View, Text, Button, ActivityIndicator, Alert } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';
import { Audio } from 'expo-av';

const API_BASE = 'http://localhost:8888';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);

  const pickFileAndUpload = async () => {
    const doc = await DocumentPicker.getDocumentAsync({
      type: ['text/plain', 'application/pdf', 'application/epub+zip'],
    });
    if (doc.canceled) return;

    setLoading(true);
    try {
      const result = await FileSystem.uploadAsync(
        `${API_BASE}/generate/music`,
        doc.assets[0].uri,
        {
          fieldName: 'file',
          httpMethod: 'POST',
          uploadType: FileSystem.FileSystemUploadType.MULTIPART,
          parameters: { book_id: 'demo', page: '1' },
        }
      );

      const data = JSON.parse(result.body);
      if (!data.download_url) throw new Error('No download URL');

      const url = `${API_BASE}${data.download_url}`;
      const { sound } = await Audio.Sound.createAsync({ uri: url });
      setPlaying(true);
      await sound.playAsync();
    } catch (e) {
      console.error(e);
      Alert.alert('Error', 'Failed to generate music');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ fontSize: 24, marginBottom: 20 }}>Readning Mobile</Text>
      <Button title="Select File" onPress={pickFileAndUpload} />
      {loading && <ActivityIndicator style={{ marginTop: 20 }} />}
      {playing && <Text style={{ marginTop: 20 }}>Playing generated music...</Text>}
    </View>
  );
}
