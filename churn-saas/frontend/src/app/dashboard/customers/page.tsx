import Link from "next/link";
import {CustomerList} from "@/features/cutomers/components/customer-list"

export default function CustomersPage() {
  return (
    <>
      <nav className="flex gap-4 p-6">
        <Link
          href="/dashboard/customers"
          className="font-medium text-white underline"
        >
          Clients
        </Link>

        <Link
          href="/dashboard/imports"
          className="font-medium text-white underline"
        >
          Importer un CSV
        </Link>
      </nav>

      <CustomerList />
    </>
  );
}