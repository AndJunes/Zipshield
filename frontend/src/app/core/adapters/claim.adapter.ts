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
  user_id: string;
  object: 'car' | 'laptop' | 'package';
  conversation: string;
  image_urls: string[];
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
  input: Pick<ClaimCase, 'userId' | 'object' | 'conversation' | 'imageUrls'>,
): ApiClaimCreate {
  return {
    user_id: input.userId,
    object: input.object,
    conversation: input.conversation,
    image_urls: input.imageUrls,
  };
}
