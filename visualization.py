import plotly.graph_objects as go

def draw_wall_3d(inputs, repeat=1):
    H = inputs.H
    B = inputs.B
    Toe = inputs.toe
    Heel = inputs.heel
    t_stem_b = inputs.t_stem_bottom
    t_stem_t = inputs.t_stem_top
    t_base = inputs.t_base
    s_cf = inputs.s_cf
    t_cf = inputs.t_cf
    
    fig = go.Figure()
    
    def add_box(x0, x1, y0, y1, z0, z1, color, name, showlegend=False):
        x = [x0, x0, x1, x1, x0, x0, x1, x1]
        y = [y0, y1, y1, y0, y0, y1, y1, y0]
        z = [z0, z0, z0, z0, z1, z1, z1, z1]
        return go.Mesh3d(x=x, y=y, z=z, i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color=color, opacity=1.0, name=name, alphahull=0, showlegend=showlegend)

    fig.add_trace(add_box(0, B, 0, t_base, 0, repeat*s_cf, 'gray', 'Base', True))
    
    back_x = Toe + t_stem_b
    front_x_bot = Toe
    front_x_top = back_x - t_stem_t
    
    xs = [front_x_bot, front_x_top, back_x, back_x, front_x_bot, front_x_top, back_x, back_x]
    ys = [t_base, H, H, t_base, t_base, H, H, t_base]
    zs = [0, 0, 0, 0, repeat*s_cf, repeat*s_cf, repeat*s_cf, repeat*s_cf]
    
    fig.add_trace(go.Mesh3d(x=xs, y=ys, z=zs, i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color='lightgray', name='Stem', showlegend=True))
    
    def add_cf(z_center, idx):
        z_start = z_center - t_cf/2
        z_end = z_center + t_cf/2
        x_cf = [back_x, back_x, B, back_x, back_x, B]
        y_cf = [H, t_base, t_base, H, t_base, t_base]
        z_cf = [z_start, z_start, z_start, z_end, z_end, z_end]
        return go.Mesh3d(x=x_cf, y=y_cf, z=z_cf, color='darkgray', name='Counterfort', alphahull=0, showlegend=(idx==0))
        
    for i in range(repeat + 1):
        fig.add_trace(add_cf(i * s_cf, i))
    
    if inputs.d_key > 0:
        k_x = Toe + t_stem_b/2 
        fig.add_trace(add_box(k_x - inputs.w_key/2, k_x + inputs.w_key/2, -inputs.d_key, 0, 0, repeat*s_cf, 'brown', 'Key', True))

    fig.update_layout(scene=dict(aspectmode='data'), title=f"3D Wall Sketch ({repeat} Bays)", height=600)
    return fig
