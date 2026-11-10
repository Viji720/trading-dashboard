import Link from 'next/link';
import { notFound } from 'next/navigation';
import { strategies } from '../../../lib/strategies';
import StrategyResults from '../../../components/StrategyResults';

export default async function StrategyPage({ params }: { params: Promise<{ strategy: string }> }) {
  const { strategy } = await params;
  if (!Object.hasOwn(strategies, strategy)) notFound();
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Link className="text-cyan-300" href="/strategies">All strategies</Link>
      <h1 className="my-4 text-3xl font-semibold">{strategies[strategy as keyof typeof strategies]}</h1>
      <StrategyResults strategy={strategy} />
    </main>
  );
}
