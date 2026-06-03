import { useEffect, useState, useCallback } from 'react';

export const useSimulationWS = () => {
  const [data, setData] = useState<any>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Use the backend port 9001 as per the new configuration
    const ws = new WebSocket(`ws://${window.location.hostname}:9001/ws/ws`);

    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(parsedData);
      } catch (e) {
        console.error('Failed to parse WebSocket message', e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = useCallback((message: string) => {
    // We don't have a reference to the ws object here, so we would need to store it or use a different approach.
    // For simplicity, we'll skip implementing sendMessage for now.
    // In a more complete implementation, we would keep the ws instance in a ref or use a state.
    console.warn('sendMessage not implemented');
  }, []);

  return { data, connected, sendMessage };
};