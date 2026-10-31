import { ClaimCase } from '../models';

export interface ApiClaim {
  id: number;
  user_id: string;
  object: 'car' | 'laptop' | 'package';
  conversation: string;
  image_urls: string[];
  evidence_standard_met: boolean;
  evidence_standard_met_reason: string;
  risk_flags: string[];
  issue_type: string;
  object_part: string;
  claim_status: 'supported' | 'contradicted' | 'not_enough_information';
  claim_status_justification: string;
  supporting_image_ids: string[];
  valid_image: boolean;
  severity: string;
  created_at: string;
  policy_id: number | null;
  date_of_loss: string | null;
}

export type ApiClaimPatch = Partial<{
  object: 'car' | 'laptop' | 'package';
  conversation: string;
  image_urls: string[];
  evidence_standard_met: boolean;
  evidence_standard_met_reason: string;
  risk_flags: string[];
  issue_type: string;
  object_part: string;
  claim_status: 'supported' | 'contradicted' | 'not_enough_information';
  claim_status_justification: string;
  supporting_image_ids: string[];
  valid_image: boolean;
  severity: string;
}>;

export interface ApiClaimCreate {
  object: 'car' | 'laptop' | 'package';
  conversation: string;
  image_urls: string[];
  policy_id: number;
  date_of_loss: string | null;
}

export function toClaimCase(api: ApiClaim): ClaimCase {
  return {
    id: api.id,
    userId: api.user_id,
    object: api.object,
    conversation: api.conversation,
    imageUrls: api.image_urls ?? [],
    evidenceStandardMet: api.evidence_standard_met,
    evidenceStandardMetReason: api.evidence_standard_met_reason,
    riskFlags: api.risk_flags ?? [],
    issueType: api.issue_type,
    objectPart: api.object_part,
    claimStatus: api.claim_status,
    claimStatusJustification: api.claim_status_justification,
    supportingImageIds: api.supporting_image_ids ?? [],
    validImage: api.valid_image,
    severity: api.severity as ClaimCase['severity'],
    policyId: api.policy_id ?? null,
    dateOfLoss: api.date_of_loss ?? null,
  };
}

export function fromClaimPartial(partial: Partial<ClaimCase>): ApiClaimPatch {
  const out: ApiClaimPatch = {};
  if (partial.object !== undefined) out.object = partial.object;
  if (partial.conversation !== undefined) out.conversation = partial.conversation;
  if (partial.imageUrls !== undefined) out.image_urls = partial.imageUrls;
  if (partial.evidenceStandardMet !== undefined) out.evidence_standard_met = partial.evidenceStandardMet;
  if (partial.evidenceStandardMetReason !== undefined) out.evidence_standard_met_reason = partial.evidenceStandardMetReason;
  if (partial.riskFlags !== undefined) out.risk_flags = partial.riskFlags;
  if (partial.issueType !== undefined) out.issue_type = partial.issueType;
  if (partial.objectPart !== undefined) out.object_part = partial.objectPart;
  if (partial.claimStatus !== undefined) out.claim_status = partial.claimStatus;
  if (partial.claimStatusJustification !== undefined) out.claim_status_justification = partial.claimStatusJustification;
  if (partial.supportingImageIds !== undefined) out.supporting_image_ids = partial.supportingImageIds;
  if (partial.validImage !== undefined) out.valid_image = partial.validImage;
  if (partial.severity !== undefined) out.severity = partial.severity;
  return out;
}

export function fromClaimCreate(
  input: Pick<ClaimCase, 'object' | 'conversation' | 'imageUrls' | 'dateOfLoss'> & {
    policyId: number;
  },
): ApiClaimCreate {
  // The claimant is derived server-side from the policy, so no user_id is sent.
  return {
    object: input.object,
    conversation: input.conversation,
    image_urls: input.imageUrls,
    policy_id: input.policyId,
    date_of_loss: input.dateOfLoss ?? null,
  };
}
