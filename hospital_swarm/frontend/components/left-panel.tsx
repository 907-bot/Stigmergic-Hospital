import { useSimulationWS } from '@/hooks/useSimulationWS';
import styles from '@/styles/left-panel.module.css';

export default function LeftPanel() {
  const { data } = useSimulationWS();
  
  // Extract stats from data if available
  const patientsGenerated = data?.simulation?.stats?.patients_generated || 0;
  const pheromonesCreated = data?.simulation?.stats?.pheromones_created || 0;
  const agentsActions = data?.simulation?.stats?.agents_actions || 0;

  return (
    <div className={styles.panel}>
      <h2 className={styles.title}>Hospital Resources</h2>
      <div className={styles.resources}>
        <div className={styles.resourceItem}>
          <span className={styles.label}>ER:</span>
          <span className={styles.value}>Available</span>
        </div>
        <div className={styles.resourceItem}>
          <span className={styles.label}>ICU:</span>
          <span className={styles.value}>Available</span>
        </div>
        <div className={styles.resourceItem}>
          <span className={styles.label}>Ward A:</span>
          <span className={styles.value}>Available</span>
        </div>
        <div className={styles.resourceItem}>
          <span className={styles.label}>Ward B:</span>
          <span className={styles.value}>Available</span>
        </div>
        <div className={styles.resourceItem}>
          <span className={styles.label}>Lab:</span>
          <span className={styles.value}>Available</span>
        </div>
        <div className={styles.resourceItem}>
          <span className={styles.label}>Pharmacy:</span>
          <span className={styles.value}>Available</span>
        </div>
      </div>
      
      <div className={styles.statsSection}>
        <h3 className={styles.statsTitle}>Simulation Stats</h3>
        <div className={styles.statsItem}>
          <span className={styles.statsLabel}>Patients Generated:</span>
          <span className={styles.statsValue}>{patientsGenerated}</span>
        </div>
        <div className={styles.statsItem}>
          <span className={styles.statsLabel}>Pheromones Created:</span>
          <span className={styles.statsValue}>{pheromonesCreated}</span>
        </div>
        <div className={styles.statsItem}>
          <span className={styles.statsLabel}>Agent Actions:</span>
          <span className={styles.statsValue}>{agentsActions}</span>
        </div>
      </div>
    </div>
  );
}