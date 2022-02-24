import { Timestamp } from "firebase/firestore";
import { StorageReference } from "firebase/storage";

export interface IAnswerAttributes {
  videoUrl: StorageReference | string;
  isSubmission: boolean;
}

export interface IAnswer extends IAnswerAttributes {
  createdAt: Timestamp;
}