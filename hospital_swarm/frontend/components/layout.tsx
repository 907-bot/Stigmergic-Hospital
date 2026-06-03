import Head from 'next/head';
import styles from '@/styles/layout.module.css';
import LeftPanel from './left-panel';
import CenterPanel from './center-panel';
import RightPanel from './right-panel';
import BottomPanel from './bottom-panel';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Head>
        <title>Stigmergic Hospital Swarm OS</title>
        <meta name="description" content="Stigmergic Hospital Swarm OS Dashboard" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div className={styles.container}>
        <div className={styles.leftPanel}>
          <LeftPanel />
        </div>
        <div className={styles.centerPanel}>
          <CenterPanel />
        </div>
        <div className={styles.rightPanel}>
          <RightPanel />
        </div>
        <div className={styles.bottomPanel}>
          <BottomPanel />
        </div>
      </div>
    </>
  );
}