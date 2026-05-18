import ProductClient from './ProductClient';

const PRODUCT_SLUGS = [
  'coconut-oil',
  'almond-oil',
  'neem-facewash',
  'boroplus-cream',
  'moisturizing-cream',
];

export function generateStaticParams() {
  return PRODUCT_SLUGS.map((slug) => ({ slug }));
}

export default function ProductPage({ params }: { params: { slug: string } }) {
  return <ProductClient slug={params.slug} />;
}
