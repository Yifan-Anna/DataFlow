import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AgentEval · Agent 质量评测平台',
  description: '基于真实执行轨迹的 Agent 自动化评测与质量分析平台',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
