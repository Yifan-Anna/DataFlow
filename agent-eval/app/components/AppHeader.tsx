'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/', label: 'Agent Playground' },
  { href: '/evaluation', label: '自动化评测' },
];

export function AppHeader() {
  const pathname = usePathname();
  return (
    <header className="app-header">
      <div className="page-container">
        <div className="title-row">
          <div>
            <div className="eyebrow">AGENT QUALITY LAB</div>
            <h1 className="app-title">Agent Evaluation Platform</h1>
            <p className="app-subtitle">真实 Tool Calling、Execution Trace 与多维评测的一体化平台</p>
          </div>
          <div className="model-pill"><span className="live-dot" />DataPilot · gpt-5.4-nano</div>
        </div>
        <nav className="top-nav" aria-label="主要导航">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return <Link className={active ? 'nav-item active' : 'nav-item'} href={item.href} key={item.href}>{item.label}</Link>;
          })}
        </nav>
      </div>
    </header>
  );
}
