import { Suspense } from "react";
import { Workspace } from "@/components/layout/Workspace";
import { ListingReports } from "@/components/candidate/ListingReports";

export default function ReportsPage() { return <Workspace role="candidate"><Suspense><ListingReports /></Suspense></Workspace>; }
