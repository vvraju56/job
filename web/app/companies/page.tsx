import type { Metadata } from "next";

import { CompaniesGrid } from "@/components/companies/companies-grid";
import { serverApi } from "@/lib/server-api";

export const metadata: Metadata = {
  title: "Companies",
  description:
    "Discover companies hiring on Makeable Jobs — company profiles, open positions, industries and reviews.",
};

export default async function CompaniesPage() {
  const companies = await serverApi.companies(48).catch(() => []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Companies</h1>
        <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
          Explore companies hiring right now. View their open positions, industry and
          company overview.
        </p>
      </div>
      <CompaniesGrid companies={companies} loading={companies.length === 0} />
    </div>
  );
}