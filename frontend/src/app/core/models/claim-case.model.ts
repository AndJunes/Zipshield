export type ClaimObject = 'car' | 'laptop' | 'package';
export type ClaimCaseStatus = 'supported' | 'contradicted' | 'not_enough_information';
export type ClaimSeverity = 'low' | 'medium' | 'high' | 'unknown' | 'none';
export type ClaimAnalysisStatus = 'none' | 'pending' | 'done' | 'failed';

export interface ClaimChatTurn {
  speaker: string;
  text: string;
}

export interface ClaimCase {
  id: number;
  userId: string;
  object: ClaimObject;
  conversation: string;
  imageUrls: string[];
  evidenceStandardMet: boolean;
  evidenceStandardMetReason: string;
  riskFlags: string[];
  issueType: string;
  objectPart: string;
  claimStatus: ClaimCaseStatus;
  claimStatusJustification: string;
  supportingImageIds: string[];
  validImage: boolean;
  severity: ClaimSeverity;
  analysisStatus: ClaimAnalysisStatus;
  policyId?: number | null;
  dateOfLoss?: string | null;
}
