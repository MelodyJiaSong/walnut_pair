// Root Layout Component

import { Layout } from 'antd';
import ReduxProvider from '@/store/ReduxProvider__component';
import TopMenu from '@/components/layout/topMenu';
import LeftSidebar from '@/components/layout/leftSidebar';
import MainPanel from '@/components/layout/mainPanel';
import '@/styles/index.scss';
import './layout__style.scss';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ReduxProvider>
          <Layout className="app-layout">
            <TopMenu />
            <Layout>
              <LeftSidebar />
              <MainPanel>{children}</MainPanel>
            </Layout>
          </Layout>
        </ReduxProvider>
      </body>
    </html>
  );
}

