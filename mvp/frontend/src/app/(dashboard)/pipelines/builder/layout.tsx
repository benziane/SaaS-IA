import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Pipeline Builder - Visual DAG Editor | SaaS-IA',
  description:
    'Visual drag-and-drop pipeline builder for creating AI workflows. Chain AI operations, data transformations, and outputs into powerful automated pipelines.',
};

export default function PipelineBuilderLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
