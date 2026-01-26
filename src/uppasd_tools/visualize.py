##########################################################################################
# visualize.py
#
# Functions for visualization of UppASD output data.
#
##########################################################################################

from .uppout import UppOut

import py3Dmol

##########################################################################################

def visualize_supercell(
    uppout: UppOut,
    x="x", y="y", z="z",
    type_col="at_type",
    width=700, height=500,
    scale=0.15,
    orthographic=True,
    xlim: tuple[float | None, float | None] | None = None,
    ylim: tuple[float | None, float | None] | None = None,
    zlim: tuple[float | None, float | None] | None = None,
    type_to_symbol=None,
    symbol_to_color=None,
    symbol_to_scale=None,
    show_sticks=False,
    stick_radius=0.08,
):
    """
    Render atoms from UppOut coord data using py3Dmol.
    
    Parameters:
        uppout (UppOut): An instance of the UppOut class containing parsed output data.
        x, y, z (str): Column names for the x, y, z coordinates.
        type_col (str): Column name for the atom type.
        width, height (int): Dimensions of the 3D view.
        scale (float): Base scale for atom spheres.
        orthographic (bool): Whether to use orthographic projection.
        xlim, ylim, zlim (tuple[float | None, float | None] | None): Optional axis limits.
        type_to_symbol (dict): Mapping from atom type to element symbol (or pseudo-symbol).
        symbol_to_color (dict): Optional mapping from symbol to color.
        symbol_to_scale (dict): Optional mapping from symbol to scale.
        show_sticks (bool): Whether to show sticks between atoms.
        stick_radius (float): Radius of the sticks if shown.
        
    Returns:
        py3Dmol.view: A py3Dmol view object with the rendered atoms.
    """
    # Validate input
    if not isinstance(uppout, UppOut):
        raise TypeError("uppout must be an UppOut instance.")

    # Read coordinate data
    df = uppout.read_coord()
    
    # Apply axis limits
    m = df.index == df.index
    if xlim is not None:
        xmin, xmax = xlim
        if xmin is not None:
            m &= df[x] >= xmin
        if xmax is not None:
            m &= df[x] <= xmax
    if ylim is not None:
        ymin, ymax = ylim
        if ymin is not None:
            m &= df[y] >= ymin
        if ymax is not None:
            m &= df[y] <= ymax
    if zlim is not None:
        zmin, zmax = zlim
        if zmin is not None:
            m &= df[z] >= zmin
        if zmax is not None:
            m &= df[z] <= zmax
    df = df[m]

    if type_to_symbol is None:
        # Fallback: assign a unique pseudo-symbol per atom type.
        uniq = sorted(set(int(t) for t in df[type_col].values))
        type_to_symbol = {t: f"X{t}" for t in uniq}

    # XYZ text
    lines = [str(len(df)), "generated from UppOut coord data"]
    for _, r in df.iterrows():
        t = int(r[type_col])
        sym = type_to_symbol.get(t, "X")
        lines.append(f"{sym} {float(r[x]):.6f} {float(r[y]):.6f} {float(r[z]):.6f}")
    xyz = "\n".join(lines)

    view = py3Dmol.view(width=width, height=height)
    view.addModel(xyz, "xyz")

    # Base style
    base_style = {"sphere": {"scale": float(scale)}}
    if show_sticks:
        base_style["stick"] = {"radius": float(stick_radius)}
    view.setStyle(base_style)

    # Orthographic projection (useful for crystals)
    if orthographic:
        view.setProjection("orthographic")

    # Per-symbol overrides: colors / sizes
    if symbol_to_color:
        for sym, col in symbol_to_color.items():
            view.setStyle({"elem": sym}, {"sphere": {"color": col, "scale": float(scale)}})

    if symbol_to_scale:
        for sym, sc in symbol_to_scale.items():
            # Preserve color if already set; py3Dmol overrides styles.
            style = {"sphere": {"scale": float(sc)}}
            if symbol_to_color and sym in symbol_to_color:
                style["sphere"]["color"] = symbol_to_color[sym]
            view.setStyle({"elem": sym}, style)

    view.zoomTo()
    return view
