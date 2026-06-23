export type ClaimObject = 'car' | 'laptop' | 'package';
export type ClaimCaseStatus = 'supported' | 'contradicted' | 'not_enough_information';
export type ClaimSeverity = 'low' | 'medium' | 'high' | 'unknown' | 'none';

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
}
