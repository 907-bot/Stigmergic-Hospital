import type { AppProps } from 'next/app';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '@/components/layout';

const standalonePages = ['/nurse', '/doctor', '/icu', '/lab', '/pharmacy', '/ambulance', '/journey', '/patient', '/login', '/admin'];

function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const isStandalone = standalonePages.includes(router.pathname);
  const isLoginPage = router.pathname === '/login';

  if (isStandalone) {
    return <Component {...pageProps} />;
  }

  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  );
}

export default MyApp;
