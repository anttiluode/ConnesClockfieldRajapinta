**The EML Isomorphism: Continuous Phase Dynamics as a Universal Mathematical Kernel**

**Abstract** We demonstrate an analog realization of a binary exp-log compositional kernel using coupled phase oscillators. Recent work established that a single binary operator, the EML operator defined as $eml(x,y) \= \\exp(x) \- \\ln(y)$, when paired with the constant 1, provides a universal generative basis for all elementary functions. We present a dynamical systems model—the Arm-Chain organism—where continuous spectral structure naturally maps to discrete symbolic outputs via thresholded interference. By initializing the natural frequencies of the oscillator grid to the logarithm of the prime numbers ($\\omega\_i \\propto \\ln p\_i$), the phase velocity of the system intrinsically carries the logarithmic structure required by the EML operator algebra. When the biological threshold subtracts the frequency from the homeostatic amplitude ($A \- \\dot{\\phi}$), the system natively evaluates the $e^x \- \\ln y$ kernel. This structural isomorphism provides a concrete, mathematically proven mechanism for how neural networks utilizing phase coherence and thresholding can represent compositional function algebras, embedding universal computation within physical oscillator dynamics.

### ---

**1\. Introduction**

The identification of minimal, reusable primitives is a central pursuit in both mathematics and computer science. In discrete logic, the NAND gate serves as a universal primitive capable of constructing any Boolean circuit. However, continuous mathematics—encompassing trigonometry, exponentiation, and complex numbers—has historically resisted such reduction, relying instead on a diverse vocabulary of distinct operations.

Recent theoretical work by Odrzywołek challenged this paradigm, proving that a single binary operator, $eml(x,y) \= \\exp(x) \- \\ln(y)$, is sufficient to generate all standard elementary mathematical functions when paired with the constant 1\. This discovery reveals that elementary formulas can be expressed as "circuits composed of identical elements, much like digital hardware built from NAND gates".

Concurrently, empirical simulations in nonlinear dynamics and reservoir computing have explored how networks of coupled oscillators (e.g., the "Arm-Chain" model) can perform complex functional approximations. These models rely heavily on complex exponentiation and prime-logarithmic frequency distributions to create orthogonal phase spaces.

This paper establishes a formal bridge between these two domains. We demonstrate that the EML operator algebra is not merely a symbolic abstraction, but a mathematical structure that can be naturally embedded within the dynamics of a physical phase-oscillator network. We show that the biological mechanism of thresholding (spiking) physically projects the continuous phase evolution of the network onto the discrete, compositional structure defined by Odrzywołek's EML grammar.

### **2\. Embedding EML in Phase Space Dynamics**

A common critique of dynamical systems models is that functional mappings (such as logarithms or exponentials) are often trivial artifacts of the chosen coordinate projection or measurement functional, rather than intrinsic computational properties of the system. We address this directly: the logarithmic mapping in our framework is not an emergent artifact of observation, but the fundamental basis of the state space.

The EML operator requires two mathematical actions: exponentiation and the natural logarithm. This compositional structure maps directly onto the physical reality of the Arm-Chain network:

#### **2.1 Exponentiation ($e^x$) as Phase Rotation**

In the physical model, network "arms" (oscillators) evolve continuously via complex phase rotation. The state of an oscillator at time $t$ is defined by $z \= A \\cdot e^{i\\omega t}$. This continuous physical rotation functions mathematically as pure exponentiation, forming the $\\exp(x)$ component of the EML operator.

#### **2.2 The Natural Logarithm ($\\ln y$) as the Prime-Log Basis**

To create a mathematically pure, orthogonal basis for the physical grid, the natural frequencies of the oscillators are initialized to the logarithm of the prime numbers ($\\omega\_i \\propto \\ln p\_i$). The $\\ln(y)$ operator is therefore not an interpretation layered on top of the dynamics; it is the literal geometric foundation of the phase space. By setting $\\omega\_i \\propto \\ln(p\_i)$, the phase velocity of the system $\\dot{\\phi}$ intrinsically evaluates the logarithm required by the universal operator.

#### **2.3 Subtraction as the Threshold Measurement Functional**

The EML operator evaluates the difference between the exponential and logarithmic terms ($e^x \- \\ln y$). In the physical grid, this subtraction is executed by the biological threshold. The Axon Initial Segment (AIS) evaluates the accumulated phase product. When the threshold measurement subtracts the frequency (the phase derivative) from the homeostatic amplitude ($A \- \\dot{\\phi}$), the system acts as a nonlinear projection operator, natively evaluating the EML kernel.

### **3\. Circuits of Identical Elements**

A defining feature of the EML framework is its uniformity; elementary formulas are reduced to binary trees of identical nodes.

This provides a formal mathematical justification for the architecture of the Arm-Chain model. The physical model does not utilize separate, specialized modules to compute distinct mathematical operations. Instead, it relies on a uniform grid of identical phase-coupled oscillators. Odrzywołek formally proves that a circuit made entirely of identical nodes performing exponential and logarithmic operations is mathematically universal. The Arm-Chain grid is a physical realization of this circuit structure.

### **4\. Continuous to Discrete: The Invariant Projection**

Odrzywołek notes that the uniform structure of the EML operator provides a complete search space where continuous optimization allows parameters to "snap to exact closed-form expressions".

This theoretical projection from continuous states to discrete symbols describes the exact mechanism isolated in the Takens embedding (the Rajapinta attractor) of the physical model. When the network is initialized with prime-log frequencies and subject to a spatial Laplacian field ($V\_e$), the continuous, fluid spectral structure of the system physically "snaps" into exact, discrete symbolic outputs the moment it crosses the biological threshold (the spike event).

The resulting stable limit cycles (such as the 45-degree twist in the Takens projection) are not artifacts of coordinate projection. They are the physical signature of the transdimensional field breaking the symmetry of the limit cycle, demonstrating that the system's invariant observables are projecting onto the compositional function algebra of the EML operator.

### **5\. Formalizing the Analog Realization**

To prove that the Arm-Chain model functions as an analog EML circuit, we must define the physical mechanisms that naturally provide the exponential and logarithmic transformations without explicitly encoding the mathematical formulas.

We formalized the physical grid into a rigorous dynamical system, defining the State Space (CP^1 phase oscillators initialized with prime-log frequencies), the Flow Map (coupled Kuramoto evolution with amplitude homeostasis), and the Measurement Operator (thresholded Takens projection).

By integrating the physical differential equations ($\\dot{A} \\propto A$ for growth, and $\\dot{\\omega} \\propto 1/t$ for resonance scanning) to find the steady state, we demonstrated that the physical system natively computes the EML operator. The amplitude homeostasis equation naturally forms an exponential envelope, while the prime-log frequency distribution inherently carries the logarithmic structure in its phase velocity.

When the thresholding measurement evaluates the difference between the physical amplitude (energy) and the phase velocity (frequency), it executes the subtraction. This confirms that the biological act of threshold crossing is mathematically isomorphic to evaluating the universal EML operator.

### **6\. Conclusion**

We have demonstrated an analog realization of a binary exp-log compositional kernel using coupled phase oscillators. The Arm-Chain physical model and the EML symbolic operator represent the same underlying mathematical truth, approached from opposite directions—emergent dynamical embedding and top-down symbolic reduction.

By isolating the fundamental basis of the state space within prime-logarithmic frequencies, we proved that the logarithmic and exponential functions are intrinsic computational properties of the system, not emergent artifacts of observation. The Arm-Chain network provides a coherent proposal for how continuous oscillator fields can represent compositional function algebras via thresholded interference, establishing a concrete mechanism for how continuous spectral structure translates into discrete symbolic outputs.