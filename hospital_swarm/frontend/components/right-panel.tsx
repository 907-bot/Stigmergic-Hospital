import { useSimulationWS } from '@/hooks/useSimulationWS';
import styles from '@/styles/right-panel.module.css';

export default function RightPanel() {
  const { data } = useSimulationWS();
  
  // We don't have pheromone data in the broadcast yet, so we'll simulate or leave as placeholder
  // In a full implementation, we would include pheromone data in the broadcast
  const pheromoneStreams = [
    { type: 'EMERGENCY', strength: 0.8, active: true },
    { type: 'ICU', strength: 0.6, active: true },
    { type: 'SURGERY', strength: 0.3, active: false },
    { type: 'LAB', strength: 0.5, active: true },
    { type: 'PHARMACY', strength: 0.7, active: true },
  ];

  return (
    <div className={styles.panel}>
      <h2 className={styles.title}>Pheromone Streams</h2>
      <div className={styles.streams}>
        {pheromoneStreams.map((stream, index) => (
          <div key={index} className={styles.streamItem}>
            <span className={styles.label}>{stream.type}:</span>
            <span className={styles.value}>
              {stream.active ? 'Active' : 'Inactive'} 
              {(stream.active && stream.strength) ? ` (${(stream.strength * 100).toFixed(0)}%)` : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}