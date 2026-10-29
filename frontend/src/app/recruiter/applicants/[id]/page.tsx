import { Workspace } from "@/components/layout/Workspace";
import { ApplicantReview } from "@/components/recruiter/ApplicantReview";
export default async function ApplicantReviewPage({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <Workspace role="recruiter"><ApplicantReview id={id} /></Workspace>; }
