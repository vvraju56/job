import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { Providers } from "@/components/layout/providers";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  title: {
    default: "Makeable Jobs — One Search. Every Opportunity.",
    template: "%s | Makeable Jobs",
  },
  description:
    "Makeable Jobs aggregates job listings from LinkedIn, Indeed, Naukri, Internshala, Wellfound and company career pages. Search every opportunity in one place and apply on the original website.",
  keywords: [
    "jobs",
    "job search",
    "makeable jobs",
    "find jobs",
    "remote jobs",
    "LinkedIn jobs",
    "Indeed jobs",
    "Naukri jobs",
    "Internshala",
  ],
  openGraph: {
    type: "website",
    siteName: "Makeable Jobs",
    title: "Makeable Jobs — One Search. Every Opportunity.",
    description:
      "Search every job opportunity across the world's top job portals in one place.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Makeable Jobs — One Search. Every Opportunity.",
    description:
      "Search every job opportunity across the world's top job portals in one place.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

const brandJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Makeable Jobs",
  alternateName: "Makeable",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  slogan: "One Search. Every Opportunity.",
  potentialAction: {
    "@type": "SearchAction",
    target: `${process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"}/jobs?q={search_term_string}`,
    "query-input": "required name=search_term_string",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-white">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(brandJsonLd) }}
        />
        <Providers>
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}