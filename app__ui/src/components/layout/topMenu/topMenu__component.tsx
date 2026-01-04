'use client';

// Top Menu Component

import { Layout } from 'antd';
import './topMenu__style.scss';

const { Header } = Layout;

export default function TopMenu() {
  return (
    <Header className="top-menu">
      <div className="top-menu__brand">
        <h1>Walnut Pair Application</h1>
      </div>
      {/* Future: User menu, notifications, etc. */}
    </Header>
  );
}

