'use client';

// Left Sidebar Component

import { useState } from 'react';
import { Layout, Menu } from 'antd';
import { useRouter, usePathname } from 'next/navigation';
import { menuItems } from './menuConfig__constant';
import { LeftSidebarProps } from './leftSidebar__type';
import './leftSidebar__style.scss';

const { Sider } = Layout;

export default function LeftSidebar({ collapsed: externalCollapsed, onCollapse }: LeftSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [internalCollapsed, setInternalCollapsed] = useState(false);

  const collapsed = externalCollapsed !== undefined ? externalCollapsed : internalCollapsed;

  const handleCollapse = (newCollapsed: boolean) => {
    if (onCollapse) {
      onCollapse(newCollapsed);
    } else {
      setInternalCollapsed(newCollapsed);
    }
  };

  // Convert menu items to Ant Design Menu format
  const menuItemsToAntMenu = (items: typeof menuItems) => {
    return items.map((item) => {
      const IconComponent = item.icon as React.ComponentType;
      if (item.children && item.children.length > 0) {
        return {
          key: item.key,
          label: item.label,
          icon: IconComponent ? <IconComponent /> : undefined,
          children: item.children.map((child) => ({
            key: child.key,
            label: child.label,
          })),
        };
      }
      return {
        key: item.key,
        label: item.label,
        icon: IconComponent ? <IconComponent /> : undefined,
      };
    });
  };

  // Find selected key based on current path
  const findSelectedKey = (): string[] => {
    for (const item of menuItems) {
      if (item.children) {
        for (const child of item.children) {
          if (child.path === pathname) {
            return [child.key];
          }
        }
      } else if (item.path === pathname) {
        return [item.key];
      }
    }
    return [];
  };

  // Handle menu item click
  const handleMenuClick = ({ key }: { key: string }) => {
    // Find the menu item by key
    const findMenuItem = (items: typeof menuItems, targetKey: string): typeof menuItems[0] | null => {
      for (const item of items) {
        if (item.key === targetKey) {
          return item;
        }
        if (item.children) {
          for (const child of item.children) {
            if (child.key === targetKey) {
              return child;
            }
          }
        }
      }
      return null;
    };

    const menuItem = findMenuItem(menuItems, key);
    if (menuItem && menuItem.path) {
      router.push(menuItem.path);
    }
  };

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={handleCollapse}
      width={200}
      className="left-sidebar"
    >
      <Menu
        mode="inline"
        selectedKeys={findSelectedKey()}
        defaultOpenKeys={['walnut-management']}
        items={menuItemsToAntMenu(menuItems)}
        onClick={handleMenuClick}
      />
    </Sider>
  );
}

