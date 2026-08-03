export type Telemetry={connected:boolean;position:{latitude:number;longitude:number;captured_at:string};heading_deg:number;speed_mps:number;front_distance_cm:number;battery_percent:number;packet_loss_percent:number;heartbeat_at:string};
export type Waypoint={id:number;x:number;y:number;type:string}; export type Route={id:'A'|'B';name:string;line_color:string;waypoints:Waypoint[]};
export type Detection={id:number;color:'red'|'green';label:string;confidence:number;center_x:number;center_y:number;radius:number};
