interface Header {
  vendor_id: number
  device_id: number
  context_id: number
  sequence_id: number
}
interface Timestamp {
  elapsed_nsec: number
}
type Vector9 =[number,number,number,number,number,number,number,number,number]
type Vector3 = [number,number,number]
type Vector4 = [number,number,number, number]
type Matrix3 = [Vector3, Vector3, Vector3]
type Matrix9 = [Vector9,Vector9,Vector9,Vector9,Vector9,Vector9,Vector9,Vector9,Vector9]
interface PositionMeasurement {
  header: Header
  time_of_validity: Timestamp
  reference_frame: number
  term1: number
  term2: number
  term3: number
  covariance: Matrix3
  error_model: number
  error_model_params: number[]
  integrity: []
}
interface PvaMeasurement {
  header: Header
  time_of_validity: Timestamp
  reference_frame: number
  p1: number
  p2: number
  p3: number
  v1: number
  v2: number
  v3: number
  quaternion: Vector4
  covariance: Matrix9
  error_model: number
  error_model_params: number[]
  integrity: []
}
export interface PositionMessage {
  wrapped_message: PositionMeasurement
  source_identifier: string
}
export interface PvaMessage {
  wrapped_message: PvaMeasurement
  source_identifier: string
}