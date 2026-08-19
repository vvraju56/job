import { CompanyCard, CompanyCardSkeleton } from "@/components/companies/company-card";
import type { Company } from "@/lib/types";

export function CompaniesGrid({
  companies,
  loading = false,
}: {
  companies: Company[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <CompanyCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {companies.map((company, i) => (
        <CompanyCard key={company.id} company={company} index={i} />
      ))}
    </div>
  );
}